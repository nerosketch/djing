# -*- coding: utf-8 -*-
from django.db import models

from djing.fields import MACAddressField
from .base_intr import DevBase
from mydefs import MyGenericIPAddressField, MyChoicesAdapter
from . import dev_types
from mapapp.models import Dot
from subprocess import run
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


DEVICE_TYPES = (
    ('Dl', dev_types.DLinkDevice),
    ('Pn', dev_types.OLTDevice),
    ('On', dev_types.OnuDevice),
    ('Ex', dev_types.EltexSwitch)
)


class DeviceDBException(Exception):
    pass


class Device(models.Model):
    ip_address = MyGenericIPAddressField()
    mac_addr = MACAddressField(null=True, blank=True, unique=True)
    comment = models.CharField(max_length=256)
    devtype = models.CharField(max_length=2, default=DEVICE_TYPES[0][0], choices=MyChoicesAdapter(DEVICE_TYPES))
    man_passw = models.CharField(max_length=16, null=True, blank=True)
    map_dot = models.ForeignKey(Dot, on_delete=models.SET_NULL, null=True, blank=True)
    user_group = models.ForeignKey('abonapp.AbonGroup', on_delete=models.SET_NULL, null=True, blank=True)
    parent_dev = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'dev'
        permissions = (
            ('can_view_device', _('Can view device')),
        )
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')

    def get_abons(self):
        pass

    def get_stat(self):
        pass

    def get_manager_klass(self):
        klasses = [kl for kl in DEVICE_TYPES if kl[0] == self.devtype]
        if len(klasses) > 0:
            res = klasses[0][1]
            if issubclass(res, DevBase):
                return res
        return

    # Можно-ли подключать устройство к абоненту
    def has_attachable_to_subscriber(self):
        mngr_class = self.get_manager_klass()
        return mngr_class.has_attachable_to_subscriber()

    def __str__(self):
        return "%s: (%s) %s %s" % (self.comment, self.get_devtype_display(), self.ip_address, self.mac_addr or '')


class Port(models.Model):
    device = models.ForeignKey(Device)
    num = models.PositiveSmallIntegerField(default=0)
    descr = models.CharField(max_length=60, null=True, blank=True)

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


def dev_post_save_signal(sender, instance, **kwargs):
    if instance.devtype != 'On':
        return
    grp = instance.user_group.pk
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
    elif grp == 80:
        code = 'uy'
    elif grp == 79 or grp == 91:
        code = 'zrk'
    newmac = str(instance.mac_addr)
    run(["%s/devapp/onu_register.sh" % settings.BASE_DIR, newmac, code])


models.signals.post_save.connect(dev_post_save_signal, sender=Device)
