from netaddr import IPNetwork, AddrFormatError
from django import forms
from django.core.exceptions import ValidationError

from ip_pool import models


class NetworkForm(forms.ModelForm):

    def clean_network(self):
        netw = self.data.get('network')
        mask = self.data.get('mask')
        if netw is None:
            return
        try:
            if mask:
                net = IPNetwork('%s/%s' % (netw, mask))
            else:
                net = IPNetwork(netw)
            return str(net.ip)
        except AddrFormatError as e:
            raise ValidationError(e, code='invalid')

    class Meta:
        model = models.NetworkModel
        fields = '__all__'
        widgets = {
            'mask': forms.TextInput(attrs={
                'pattern': '^\d{1,3}$'
            })
        }


class EmployedIpForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.fields['ip'].initial = '127.0.0.1'

    class Meta:
        model = models.EmployedIpModel
        fields = '__all__'
