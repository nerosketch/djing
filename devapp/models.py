# -*- coding: utf-8 -*-
import requests
from django.db import models, ProgrammingError
from djing.fields import MACAddressField
from .base_intr import DevBase
from mydefs import MyGenericIPAddressField, MyChoicesAdapter, ip2int
from . import dev_types
from subprocess import run
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from json.decoder import JSONDecodeError
from group_app.models import Group


DEVICE_TYPES = (
    ('Dl', dev_types.DLinkDevice),
    ('Pn', dev_types.OLTDevice),
    ('On', dev_types.OnuDevice),
    ('Ex', dev_types.EltexSwitch)
)


class DeviceDBException(Exception):
    pass


class DeviceMonitoringException(Exception):
    pass


class DeviceManager(models.Manager):
    @staticmethod
    def wrap_monitoring_info(devices_queryset):
        nag_url = getattr(settings, 'NAGIOS_URL', None)
        if nag_url is not None:
            addrs = ['h=%s' % hex(ip2int(dev.ip_address))[2:] for dev in devices_queryset]
            url = '%s/host/status/arr?%s' % (nag_url, '&'.join(addrs))
            try:
                res = requests.get(url).json()
            except (requests.exceptions.ConnectionError, JSONDecodeError) as e:
                raise DeviceMonitoringException(e)
            for dev in devices_queryset:
                inf = [x for x in res if x.get('address') == dev.ip_address]
                if len(inf) > 0:
                    setattr(dev, 'mon', inf[0].get('current_status'))
        return devices_queryset


class Device(models.Model):
    ip_address = MyGenericIPAddressField(verbose_name=_('Ip address'))
    mac_addr = MACAddressField(verbose_name=_('Mac address'), null=True, blank=True, unique=True)
    comment = models.CharField(_('Comment'), max_length=256)
    devtype = models.CharField(_('Device type'), max_length=2, default=DEVICE_TYPES[0][0], choices=MyChoicesAdapter(DEVICE_TYPES))
    man_passw = models.CharField(_('SNMP password'), max_length=16, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Device group'))
    parent_dev = models.ForeignKey('self', verbose_name=_('Parent device'), blank=True, null=True, on_delete=models.SET_NULL)

    snmp_item_num = models.PositiveSmallIntegerField(_('SNMP Number'), default=0, blank=True)

    NETWORK_STATES = (
        ('und', _('Undefined')),
        ('up', _('Up')),
        ('unr', _('Unreachable')),
        ('dwn', _('Down'))
    )
    status = models.CharField(_('Status'), max_length=3, choices=NETWORK_STATES, default='und')

    is_noticeable = models.BooleanField(_('Send notify when monitoring state changed'), default=False)

    objects = DeviceManager()

    class Meta:
        db_table = 'dev'
        permissions = (
            ('can_view_device', _('Can view device')),
        )
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        ordering = ['id']

    def get_abons(self):
        pass

    def get_status(self):
        return self.status

    def get_manager_klass(self):
        klasses = [kl for kl in DEVICE_TYPES if kl[0] == self.devtype]
        if len(klasses) > 0:
            res = klasses[0][1]
            if issubclass(res, DevBase):
                return res
        return

    def get_manager_object(self):
        man_klass = self.get_manager_klass()
        return man_klass(self)

    # Можно-ли подключать устройство к абоненту
    def has_attachable_to_subscriber(self):
        mngr_class = self.get_manager_klass()
        return mngr_class.has_attachable_to_subscriber()

    def __str__(self):
        return "%s: (%s) %s %s" % (self.comment, self.get_devtype_display(), self.ip_address, self.mac_addr or '')

    def update_dhcp(self):
        if self.devtype not in ('On','Dl'):
            return
        #raise ProgrammingError('переделать это безобразие')
        # FIXME: переделать это безобразие
        grp = self.group.id
        code = ''
        if grp == 87:
            code = 'chk'
        elif grp == 85:
            code = 'drf'
        elif grp == 86:
            code = 'eme'
        elif grp == 84:
            code = 'kunc'
        elif grp == 47:
            code = 'mtr'
        elif grp == 60:
            code = 'nvg'
        elif grp == 65:
            code = 'ohot'
        elif grp == 89:
            code = 'psh'
        elif grp == 92:
            code = 'str'
        elif grp == 80 or grp == 94:
            code = 'uy'
        elif grp == 79 or grp == 91:
            code = 'zrk'
        elif grp == 95:
            code = 'yst'
        elif grp == 96:
            code = 'lzk'
        elif grp == 51:
            code = 'sad'
        newmac = str(self.mac_addr)
        run(["%s/devapp/onu_register.sh" % settings.BASE_DIR, newmac, code])


class Port(models.Model):
    device = models.ForeignKey(Device, models.CASCADE, verbose_name=_('Device'))
    num = models.PositiveSmallIntegerField(_('Number'), default=0)
    descr = models.CharField(_('Description'), max_length=60, null=True, blank=True)

    def __str__(self):
        return "%d: %s" % (int(self.num), self.descr)

    class Meta:
        db_table = 'dev_port'
        unique_together = (('device', 'num'))
        permissions = (
            ('can_toggle_ports', _('Can toggle ports')),
        )
        verbose_name = _('Port')
        verbose_name_plural = _('Ports')



