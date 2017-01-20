# -*- coding: utf-8 -*-
from django import forms

from mydefs import ip_addr_regex


class PoolForm(forms.Form):
    start_ip = forms.GenericIPAddressField(protocol='ipv4', widget=forms.TextInput(attrs={
        'pattern': ip_addr_regex,
        'placeholder': '127.0.0.1',
        'id': 'start_ip',
        'class': 'form-control',
        'required': ''
    }), required=True)

    end_ip = forms.GenericIPAddressField(protocol='ipv4', widget=forms.TextInput(attrs={
        'pattern': ip_addr_regex,
        'placeholder': '127.0.0.1',
        'id': 'end_ip',
        'class': 'form-control',
        'required': ''
    }), required=True)
