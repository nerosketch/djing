# -*- coding: utf-8 -*-
from django.db import models

from base_intr import DevBase
from mydefs import MyGenericIPAddressField, MyChoicesAdapter
from dev_types import DEVICE_TYPES


class _DeviceChoicesAdapter(MyChoicesAdapter):
    def __init__(self):
        super(_DeviceChoicesAdapter, self).__init__(DEVICE_TYPES)


class Device(models.Model):
    ip_address = MyGenericIPAddressField()
    comment = models.CharField(max_length=256)
    devtype = models.CharField(max_length=2, default=DEVICE_TYPES[0][0], choices=_DeviceChoicesAdapter())
    man_passw = models.CharField(max_length=16, null=True, blank=True)
    # map_dot = models.ForeignKey()

    class Meta:
        db_table = 'dev'

    def get_abons(self):
        pass

    def get_stat(self):
        pass

    def get_manager_klass(self):
        klasses = filter(lambda kl: kl[0] == self.devtype, DEVICE_TYPES)
        if len(klasses) > 0:
            res = klasses[0][1]
            if issubclass(res, DevBase):
                return res
        return


class Port(models.Model):
    PORT_SPEEDS = (
        ('h', '100Mbps'),
        ('k', '1Gbps'),
        ('d', '10Gbps')
    )
    device = models.ForeignKey(Device)
    num = models.PositiveSmallIntegerField(default=0)
    speed = models.CharField(max_length=1, default=PORT_SPEEDS[0][0], choices=PORT_SPEEDS)

    class Meta:
        db_table = 'dev_port'
        unique_together = (('device', 'num'))


class PortStates(models.Model):
    port = models.OneToOneField(Port)
    state_json_info = models.TextField()
