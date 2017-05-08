# -*- coding: utf-8 -*-
from django import forms

from . import models
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
                'class': 'form-control'
            }),
            'comment': forms.Textarea(attrs={
                'required': True,
                'class': 'form-control'
            }),
            'devtype': forms.Select(attrs={
                'class': 'form-control'
            }),
            'man_passw': forms.PasswordInput(attrs={
                'class': 'form-control'
            }, render_value=True),
            'map_dot': forms.Select(attrs={
                'class': 'form-control'
            }),
            'user_group': forms.Select(attrs={
                'class': 'form-control'
            })
        }
