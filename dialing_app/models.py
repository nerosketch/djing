from django.db import models
from django.utils.translation import ugettext_lazy as _


class AsteriskCDR(models.Model):
    DISPOSITION_CHOICES = (
        ('NO ANSWER', _('No answer')),
        ('FAILED', _('Failed')),
        ('BUSY', _('Busy')),
        ('ANSWERED', _('Answered')),
        ('UNKNOWN', _('Unknown'))
    )
    calldate = models.DateTimeField(default='0000-00-00 00:00:00', primary_key=True)
    clid = models.CharField(max_length=80, default='')
    src = models.CharField(max_length=80, default='')
    dst = models.CharField(max_length=80, default='')
    dcontext = models.CharField(max_length=80, default='')
    channel = models.CharField(max_length=80, default='')
    dstchannel = models.CharField(max_length=80, default='')
    lastapp = models.CharField(max_length=80, default='')
    lastdata = models.CharField(max_length=80, default='')
    duration = models.IntegerField(default=0)
    billsec = models.IntegerField(default=0)
    start = models.DateTimeField(null=True, blank=True, default=None)
    answer = models.DateTimeField(null=True, blank=True, default=None)
    end = models.DateTimeField(null=True, blank=True, default=None)
    disposition = models.CharField(max_length=45, choices=DISPOSITION_CHOICES, default='')
    amaflags = models.IntegerField(default=0)
    accountcode = models.CharField(max_length=20, default='')
    userfield = models.CharField(max_length=255, default='')
    uniqueid = models.CharField(max_length=32, default='')

    def save(self, *args, **kwargs):
        return

    def delete(self, *args, **kwargs):
        return

    class Meta:
        abstract = True


def getModel():
    class DynamicCDR(AsteriskCDR):
        class Meta:
            abstract = False
            db_table = 'cdr'
    return DynamicCDR
