from django.db import models
from django.utils.translation import ugettext_lazy as _
from devapp.models import Device


class Dot(models.Model):
    title = models.CharField(_('Map point title'), max_length=127)
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    devices = models.ManyToManyField(Device, verbose_name=_('Devices'), db_table='dot_device')
    attachment = models.FileField(_('Attachment'), upload_to='map_attachments/%Y_%m_%d', null=True, blank=True)

    class Meta:
        db_table = 'dots'
        verbose_name = _('Map point')
        verbose_name_plural = _('Map points')
        permissions = (
            ('can_view', _('Can view')),
        )

    def __str__(self):
        return self.title
