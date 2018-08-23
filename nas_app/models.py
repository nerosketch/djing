from django.contrib.messages import MessageFailure
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.db import models
from djing.lib import MyChoicesAdapter
from nas_app.nas_managers import NAS_TYPES


class NASModel(models.Model):
    title = models.CharField(_('Title'), max_length=127, unique=True)
    ip_address = models.GenericIPAddressField(_('Ip address'), unique=True)
    ip_port = models.PositiveSmallIntegerField(_('Port'))
    auth_login = models.CharField(_('Auth login'), max_length=64)
    auth_passw = models.CharField(_('Auth password'), max_length=127)
    nas_type = models.CharField(_('Type'), max_length=4, choices=MyChoicesAdapter(NAS_TYPES), default=NAS_TYPES[0][0])
    default = models.BooleanField(_('Is default'), default=False)

    def get_nas_manager_klass(self):
        try:
            return next(klass for code, klass in NAS_TYPES if code == self.nas_type)
        except StopIteration:
            raise TypeError(_('One of nas types implementation is not found'))

    def get_nas_manager(self):
        klass = self.get_nas_manager_klass()
        if hasattr(self, '_nas_mngr'):
            o = getattr(self, '_nas_mngr')
        else:
            o = klass(
                login=self.auth_login,
                password=self.auth_passw,
                ip=self.ip_address,
                port=int(self.ip_port)
            )
            setattr(self, '_nas_mngr', o)
        return o

    def get_absolute_url(self):
        return resolve_url('nas_app:edit', self.pk)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'nas'
        verbose_name = _('Network access server. Gateway')
        verbose_name_plural = _('Network access servers. Gateways')
        ordering = 'ip_address',
        permissions = (
            ('can_view_nas', _('Can view NAS')),
        )


@receiver(pre_delete, sender=NASModel)
def nas_pre_delete(sender, **kwargs):
    nas = kwargs.get("instance")
    # check if this nas is default.
    # You cannot remove default server
    if nas.default:
        raise MessageFailure(_('You cannot remove default server'))
