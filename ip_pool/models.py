from ipaddress import ip_network, ip_address
from typing import Optional, Generator

from django.db.utils import IntegrityError
from django.shortcuts import resolve_url
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from djing.fields import MACAddressField
from djing.lib import DuplicateEntry
from ip_pool.fields import GenericIpAddressWithPrefix
from group_app.models import Group


class NetworkModel(models.Model):
    _netw_cache = None

    network = GenericIpAddressWithPrefix(
        verbose_name=_('IP network'),
        help_text=_('Ip address of network. For example: '
                    '192.168.1.0 or fde8:6789:1234:1::'),
        unique=True
    )
    NETWORK_KINDS = (
        ('inet', _('Internet')),
        ('guest', _('Guest')),
        ('trust', _('Trusted')),
        ('device', _('Devices')),
        ('admin', _('Admin'))
    )
    kind = models.CharField(
        _('Kind of network'), max_length=6,
        choices=NETWORK_KINDS, default='guest'
    )
    description = models.CharField(_('Description'), max_length=64)
    groups = models.ManyToManyField(Group, verbose_name=_('Groups'))

    # Usable ip range
    ip_start = models.GenericIPAddressField(_('Start work ip range'))
    ip_end = models.GenericIPAddressField(_('End work ip range'))

    def __str__(self):
        netw = self.get_network()
        return "%s: %s" % (self.description, netw.with_prefixlen)

    def get_network(self):
        if self.network is None:
            return
        if self._netw_cache is None:
            self._netw_cache = ip_network(self.network)
        return self._netw_cache

    def get_absolute_url(self):
        return resolve_url('ip_pool:net_edit', self.pk)

    def clean(self):
        errs = {}
        if self.network is None:
            errs['network'] = ValidationError(
                _('Network is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        net = self.get_network()
        if self.ip_start is None:
            errs['ip_start'] = ValidationError(
                _('Ip start is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        start_ip = ip_address(self.ip_start)
        if start_ip not in net:
            errs['ip_start'] = ValidationError(
                _('Start ip must be in subnet of specified network'),
                code='invalid'
            )
        if self.ip_end is None:
            errs['ip_end'] = ValidationError(
                _('Ip end is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        end_ip = ip_address(self.ip_end)
        if end_ip not in net:
            errs['ip_end'] = ValidationError(
                _('End ip must be in subnet of specified network'),
                code='invalid'
            )
        if errs:
            raise ValidationError(errs)

        other_nets = NetworkModel.objects.exclude(
            pk=self.pk
        ).only('network').order_by('network')
        if not other_nets.exists():
            return
        for onet in other_nets.iterator():
            onet_netw = onet.get_network()
            if net.overlaps(onet_netw):
                errs['network'] = ValidationError(
                    _('Network is overlaps with %(other_network)s'),
                    params={
                        'other_network': str(onet_netw)
                    }
                )
                raise ValidationError(errs)

    def get_scope(self) -> str:
        net = self.get_network()
        if net.is_global:
            return _('Global')
        elif net.is_link_local:
            return _('Link local')
        elif net.is_loopback:
            return _('Loopback')
        elif net.is_multicast:
            return _('Multicast')
        elif net.is_private:
            return _('Private')
        elif net.is_reserved:
            return _('Reserved')
        elif net.is_site_local:
            return _('Site local')
        elif net.is_unspecified:
            return _('Unspecified')
        return "I don't know"

    def get_free_ip(self, employed_ips: Optional[Generator]):
        """
        Find free ip in network.
        :param employed_ips: Sorted from less to more
         ip addresses from current network.
        :return: single finded ip
        """
        network = self.get_network()
        work_range_start_ip = ip_address(self.ip_start)
        work_range_end_ip = ip_address(self.ip_end)
        if employed_ips is None:
            for ip in network.hosts():
                if work_range_start_ip <= ip <= work_range_end_ip:
                    return ip
            return
        for ip in network.hosts():
            if ip < work_range_start_ip:
                continue
            elif ip > work_range_end_ip:
                break  # Not found
            used_ip = next(employed_ips)
            if used_ip is None:
                return ip
            used_ip = ip_address(used_ip)
            if ip < used_ip:
                return ip

    class Meta:
        db_table = 'ip_pool_network'
        verbose_name = _('Network')
        verbose_name_plural = _('Networks')
        ordering = ('network',)


# Deprecated. Remove after migrations squashed
class IpLeaseManager(models.Manager):

    def get_free_ip(self, network: NetworkModel):
        netw = network.get_network()
        work_range_start_ip = ip_address(network.ip_start)
        work_range_end_ip = ip_address(network.ip_end)
        employed_ip_queryset = self.filter(
            network=network,
            is_dynamic=False
        ).order_by('ip').only('ip')

        if employed_ip_queryset.exists():
            used_ip_gen = employed_ip_queryset.iterator()
            for net_ip in netw.hosts():
                if net_ip < work_range_start_ip:
                    continue
                elif net_ip > work_range_end_ip:
                    break
                used_ip = next(used_ip_gen, None)
                if used_ip is None:
                    return net_ip
                ip = ip_address(used_ip.ip)
                if net_ip < ip:
                    return net_ip
        else:
            for net in netw.hosts():
                if work_range_start_ip <= net <= work_range_end_ip:
                    return net

    def create_from_ip(self, ip: str, net: Optional[NetworkModel],
                       mac=None, is_dynamic=True):
        # ip = ip_address(ip)
        try:
            return self.create(
                ip=ip,
                network=net,
                is_dynamic=is_dynamic,
                mac_addr=mac
            )
        except IntegrityError as e:
            raise DuplicateEntry(e)


# Deprecated. Remove after migrations squashed
class IpLeaseModel(models.Model):
    ip = models.GenericIPAddressField(verbose_name=_('Ip address'), unique=True)
    network = models.ForeignKey(NetworkModel, on_delete=models.CASCADE,
                                verbose_name=_('Parent network'), null=True, blank=True)
    mac_addr = MACAddressField(verbose_name=_('Mac address'), null=True, blank=True)
    lease_time = models.DateTimeField(_('Lease time'), auto_now_add=True)
    device_info = models.CharField(null=True, blank=True, default=None, max_length=128)

    objects = IpLeaseManager()

    def __str__(self):
        return self.ip

    def clean(self):
        ip = ip_address(self.ip)
        network = self.network.get_network()
        if ip not in network:
            raise ValidationError(_('Ip address %(ip)s not in %(net)s network'), params={
                'ip': ip,
                'net': network
            }, code='invalid')

    class Meta:
        db_table = 'ip_pool_employed_ip'
        verbose_name = _('Employed ip')
        verbose_name_plural = _('Employed ip addresses')
        ordering = ('-id',)
        unique_together = ('ip', 'network', 'mac_addr')


# Deprecated. Remove after migrations squashed
class LeasesHistory(models.Model):
    ip = models.GenericIPAddressField(verbose_name=_('Ip address'))
    lease_time = models.DateTimeField(_('Lease time'), auto_now_add=True)
    mac_addr = MACAddressField(_('Mac address'), null=True, blank=True)

    def __str__(self):
        return self.ip

    class Meta:
        db_table = 'ip_pool_leases_history'
        verbose_name = _('History lease')
        verbose_name_plural = _('Leases history')
        ordering = '-lease_time',
