from datetime import timedelta
from ipaddress import ip_network, ip_address

from django.conf import settings
from django.shortcuts import resolve_url
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

#from djing.fields import MACAddressField
from ip_pool.fields import GenericIpAddressWithPrefix


class NetworkModel(models.Model):
    _netw_cache = None

    network = GenericIpAddressWithPrefix(
        verbose_name=_('IP network'),
        help_text=_('Ip address of network. For example: 192.168.1.0 or fde8:6789:1234:1::'),
        unique=True
    )
    NETWORK_KINDS = (
        ('inet', _('Internet')),
        ('guest', _('Guest')),
        ('trust', _('Trusted')),
        ('device', _('Devices')),
        ('admin', _('Admin'))
    )
    kind = models.CharField(_('Kind of network'), max_length=6, choices=NETWORK_KINDS, default='guest')
    description = models.CharField(_('Description'), max_length=64)

    def __str__(self):
        return "%s: %s" % (self.description, self.network)

    def get_network(self):
        if self._netw_cache is None:
            self._netw_cache = ip_network(self.network)
        return self._netw_cache

    def get_absolute_url(self):
        return resolve_url('ip_pool:net_edit', self.pk)

    class Meta:
        db_table = 'ip_pool_network'
        verbose_name = _('Network')
        verbose_name_plural = _('Networks')
        ordering = ('description',)


class IpLeaseManager(models.Manager):

    def get_free_ip(self, network: NetworkModel):
        netw = ip_network(network)
        employed_ip_queryset = self.filter(network=network)
        free_ip = next(ip_address(net) for ip, net in zip(
            employed_ip_queryset, netw
        ) if ip != net)
        return free_ip

    def create_from_ip(self, ip: str, cidr_subnet: int):
        # FIXME: get subnet
        raise NotImplementedError
        net = ip_network((ip, cidr_subnet), strict=False)
        netw_instance = NetworkModel.objects.filter(network=str(net)).first()
        if netw_instance is not None:
            return self.create(
                ip=ip,
                network=netw_instance,
                is_dynamic=True,
                is_active=True
            )

    def expired(self):
        lease_live_time = getattr(settings, 'LEASE_LIVE_TIME')
        if lease_live_time is None:
            raise ImproperlyConfigured('You must specify LEASE_LIVE_TIME in settings')
        senility = now() - timedelta(seconds=lease_live_time)
        return self.filter(lease_time__lt=senility, is_active=False)


class IpLeaseModel(models.Model):
    ip = models.GenericIPAddressField(verbose_name=_('Ip address'), unique=True)
    network = models.ForeignKey(NetworkModel, on_delete=models.CASCADE, verbose_name=_('Parent network'))
    lease_time = models.DateTimeField(_('Lease time'), auto_now_add=True)
    is_dynamic = models.BooleanField(_('Is dynamic'), default=False)
    is_active = models.BooleanField(_('Is active'), default=True)

    objects = IpLeaseManager()

    def __str__(self):
        return self.ip

    def free(self):
        if self.is_active:
            self.is_active = False
            self.save(update_fields=('is_active',))

    def start(self):
        if not self.is_active:
            self.is_active = True
            self.save(update_fields=('is_active',))

    def clean(self):
        ip = ip_address(self.ip)
        network = self.network.get_network()

        if ip not in network:
            raise ValidationError(_('Ip address %(ip)s not in %(net)s network') % {
                'ip': ip,
                'net': network
            }, code='invalid')

    class Meta:
        db_table = 'ip_pool_employed_ip'
        verbose_name = _('Employed ip')
        verbose_name_plural = _('Employed ip addresses')
        ordering = ('-id',)
        unique_together = ('ip', 'network')


# class LeasesHistory(models.Model):
#     ip = models.GenericIPAddressField(verbose_name=_('Ip address'))
#     lease_time = models.DateTimeField(_('Lease time'), auto_now_add=True)
#     mac_addr = MACAddressField(_('Mac address'), null=True, blank=True)
