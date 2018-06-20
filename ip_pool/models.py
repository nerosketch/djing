from typing import Optional

from django.shortcuts import resolve_url
from netaddr import IPNetwork, IPAddress
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class NetworkModel(models.Model):
    _netw_cache = None

    network = models.GenericIPAddressField(
        verbose_name=_('IP network'),
        help_text=_('Ip address of network. For example: 192.168.1.0 or fde8:6789:1234:1::'),
        unique=True
    )
    mask = models.PositiveSmallIntegerField(
        _('Mask'),
        help_text=_('Net mask bits length for ipv4 or prefix length for ipv6'),
        default=24,
    )
    work_range_start_ip = models.GenericIPAddressField(
        verbose_name=_('Work range start ip'),
        help_text=_('For example 192.168.1.2, this is first ip that may be used')
    )
    work_range_end_ip = models.GenericIPAddressField(
        verbose_name=_('Work range end ip'),
        help_text=_('Ip may be used until 192.168.1.254')
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
        return "%s: %s/%d" % (self.description, self.network, self.mask)

    def get_network(self) -> IPNetwork:
        if self._netw_cache is None:
            self._netw_cache = IPNetwork(self.network)
            if self.mask:
                self._netw_cache.prefixlen = self.mask
        return self._netw_cache

    def get_absolute_url(self):
        return resolve_url('ip_pool:net_edit', self.pk)

    class Meta:
        db_table = 'ip_pool_network'
        verbose_name = _('Network')
        verbose_name_plural = _('Networks')
        ordering = ('description',)


class EmployedIpManager(models.Manager):

    def get_free_ip(self, network: NetworkModel) -> Optional[IPAddress]:
        netw = IPNetwork(network)
        employed_ip_queryset = self.filter(network=network)
        free_ip = next(IPAddress(net) for ip, net in zip(
            employed_ip_queryset, netw
        ) if ip != net)
        return free_ip


class EmployedIpModel(models.Model):
    ip = models.GenericIPAddressField(verbose_name=_('Ip address'), unique=True)
    network = models.ForeignKey(NetworkModel, on_delete=models.CASCADE, verbose_name=_('Parent network'))

    objects = EmployedIpManager()

    def __str__(self):
        return self.ip

    def clean(self):
        ip = IPAddress(self.ip)
        network = self.network.get_network()

        if ip not in network:
            raise ValidationError(_('Ip address %(ip)s not in %(net)s network') % {
                'ip': ip,
                'net': network
            }, code='invalid')

        start_allowed_ip = IPAddress(self.network.work_range_start_ip)
        end_allowed_ip = IPAddress(self.network.work_range_end_ip)
        if not start_allowed_ip <= ip <= end_allowed_ip:
            raise ValidationError(_('Ip address that you entered is not in work range'), code='invalid')

    class Meta:
        db_table = 'ip_pool_employed_ip'
        verbose_name = _('Employed ip')
        verbose_name_plural = _('Employed ip addresses')
        ordering = ('-id',)
        unique_together = ('ip', 'network')
