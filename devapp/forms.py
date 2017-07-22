# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext as _
from django.db import IntegrityError

from . import models
from mydefs import ip_addr_regex
from djing import MAC_ADDR_REGEX


class DeviceForm(forms.ModelForm):
    mac_addr = forms.CharField(widget=forms.TextInput(attrs={
        'pattern': MAC_ADDR_REGEX,
        'required': True,
        'class': 'form-control'
    }), error_messages={
        'required': _('Mac address is required for fill'),
        'unique': _('Device with that mac is already exist')
    })

    class Meta:
        model = models.Device
        fields = '__all__'
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'pattern': ip_addr_regex,
                'placeholder': '192.168.0.100',
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
            }),
            'parent_dev': forms.Select(attrs={
                'class': 'form-control'
            })
        }


class PortForm(forms.ModelForm):
    class Meta:
        model = models.Port
        exclude = ['device']
        widgets = {
            'num': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'descr': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }

    def save(self, commit=True):
        try:
            super(PortForm, self).save(commit)
        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                raise models.DeviceDBException(_('Port number on device must be unique'))
            else:
                raise models.DeviceDBException(e)
