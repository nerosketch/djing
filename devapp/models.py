# -*- coding: utf-8 -*-
from django.db import models

from djing.fields import MACAddressField
from .base_intr import DevBase
from mydefs import MyGenericIPAddressField, MyChoicesAdapter
from .dev_types import DLinkDevice, OLTDevice, OnuDevice
from mapapp.models import Dot


DEVICE_TYPES = (
    ('Dl', DLinkDevice),
    ('Pn', OLTDevice),
    ('On', OnuDevice)
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
        return "%s: (%s) %s %s" % (self.comment, self.get_devtype_display(), self.ip_address, self.mac_addr)


class Port(models.Model):
    device = models.ForeignKey(Device)
    num = models.PositiveSmallIntegerField(default=0)
    descr = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        return "%d: %s" % (int(self.num), self.descr)

    class Meta:
        db_table = 'dev_port'
        unique_together = (('device', 'num'))
