from ipaddress import ip_network

from django import forms
from django.core.exceptions import ValidationError

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
