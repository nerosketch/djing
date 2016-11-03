# -*- coding: utf-8 -*-
from django import forms

import models
from mydefs import ip_addr_regex


class DeviceForm(forms.ModelForm):
    class Meta:
        model = models.Device
        fields = '__all__'
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'pattern': ip_addr_regex,
                'placeholder': '192.168.0.100',
                'required': True,
                'class': 'form-control',
                'id': 'ip_address'
            }),
            'comment': forms.Textarea(attrs={
                'required': True,
                'class': 'form-control',
                'id': 'comment'
            }),
            'devtype': forms.Select(attrs={
                'class': 'form-control',
                'id': 'devtype'
            }),
            'man_passw': forms.PasswordInput(attrs={
                'class': 'form-control',
                'id': 'man_passw'
            })
        }
