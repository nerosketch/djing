from django.db import models
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


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

    def locate_disposition(self):
        dsp = self.disposition
        if dsp == 'NO ANSWER':
            return _('No answer')
        elif dsp == 'FAILED':
            return _('Failed')
        elif dsp == 'BUSY':
            return _('Busy')
        elif dsp == 'ANSWERED':
            return _('Answered')
        elif dsp == 'UNKNOWN':
            return _('Unknown')
        return ''

    def path_to_media(self):
        path = getattr(settings, 'DIALING_MEDIA', '/media')
        if self.userfield == 'request':
            return "%s/recording/request" % path
        elif self.userfield == 'report':
            return "%s/recording/bug" % path
        return "%s/monitor" % path

    def url(self):
        if type(self.calldate) is datetime:
            return "%s/%s-%s-%s.wav" % (self.path_to_media(), self.calldate.strftime('%Y/%m/%d/%H_%M'), self.src, self.dst)

    class Meta:
        db_table = 'cdr'
        managed = False
