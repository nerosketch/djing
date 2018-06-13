from netaddr import IPNetwork, AddrFormatError, IPAddress
from django import forms
from django.core.exceptions import ValidationError
from ip_pool import models


class NetworkForm(forms.ModelForm):

    def clean_network(self):
        network = self.cleaned_data.get('network')
        try:
            return IPAddress(network)
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
