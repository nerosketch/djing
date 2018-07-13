from ipaddress import ip_network, ip_address

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from ip_pool import models


class NetworkForm(forms.ModelForm):

    def clean_network(self):
        netw = self.data.get('network')
        if netw is None:
            return
        try:
            net = ip_network(netw)
            return net.compressed
        except ValueError as e:
            raise ValidationError(e, code='invalid')

    class Meta:
        model = models.NetworkModel
        fields = '__all__'


class LeaseForm(forms.Form):
    def __init__(self, data=None, *args, **kwargs):
        super(LeaseForm, self).__init__(data=data, *args, **kwargs)
        nets = models.NetworkModel.objects.defer('groups')
        if nets.exists():
            self.fields['possible_networks'].choices = ((net.pk, str(net.get_network())) for net in nets.iterator())

    def clean_ip_addr(self):
        ip_addr = self.data.get('ip_addr')
        if ip_addr is None:
            return
        ip_addr = ip_address(ip_addr)
        net_id = self.data.get('possible_networks')
        if net_id is None:
            return ip_addr.compressed
        net = models.NetworkModel.objects.get(pk=net_id)
        if ip_addr not in net.get_network():
            raise ValidationError(_('Ip that you typed is not in subnet that you have selected'))
        if ip_addr < ip_address(net.ip_start):
            raise ValidationError(_('Ip that you have passed is less than allowed network range'))
        if ip_addr > ip_address(net.ip_end):
            raise ValidationError(_('Ip that you have passed is greater than allowed network range'))
        return ip_addr.compressed

    ip_addr = forms.GenericIPAddressField(label=_('Ip address'))
    is_dynamic = forms.BooleanField(label=_('Is dynamic'), required=False)
    possible_networks = forms.ChoiceField(label=_('Possible networks'))
