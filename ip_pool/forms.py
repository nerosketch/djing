from netaddr import IPNetwork, AddrFormatError, IPAddress
from django import forms
from django.core.exceptions import ValidationError

from ip_pool import models


class NetworkForm(forms.ModelForm):
    mask = forms.CharField(max_length=39, min_length=7, widget=forms.TextInput())

    def clean_mask(self):
        try:
            network = IPAddress(self.data.get('network'))
            mask = self.data.get('mask')
            net = IPNetwork('%s/%s' % (network, mask))
            ip, new_mask = str(net.cidr).split('/')
            return new_mask
        except AddrFormatError as e:
            raise ValidationError(e, code='invalid')

    class Meta:
        model = models.NetworkModel
        fields = '__all__'


class EmployedIpForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.fields['ip'].initial = '127.0.0.1'

    class Meta:
        model = models.EmployedIpModel
        fields = '__all__'
