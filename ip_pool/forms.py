# -*- coding: utf-8 -*-
from django import forms

from mydefs import ip_addr_regex


class PoolForm(forms.Form):
    start_ip = forms.GenericIPAddressField(protocol='IPv4', widget=forms.TextInput(attrs={
        'pattern': ip_addr_regex,
        'placeholder': u'127.0.0.1',
        'id': 'start_ip',
        'class': 'form-control',
        'required': ''
    }), required=True)

    end_ip = forms.GenericIPAddressField(protocol='IPv4', widget=forms.TextInput(attrs={
        'pattern': ip_addr_regex,
        'placeholder': u'127.0.0.1',
        'id': 'end_ip',
        'class': 'form-control',
        'required': ''
    }), required=True)
