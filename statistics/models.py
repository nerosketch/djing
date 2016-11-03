from __future__ import unicode_literals

from django.db import models

from mydefs import MyGenericIPAddressField


class StatElem(models.Model):
    src_ip = MyGenericIPAddressField()
    dst_ip = MyGenericIPAddressField()
    proto = models.PositiveSmallIntegerField(default=0)
    src_port = models.PositiveIntegerField(default=0)
    dst_port = models.PositiveIntegerField(default=0)
    octets = models.PositiveIntegerField(default=0)
    packets = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'flowstat'
