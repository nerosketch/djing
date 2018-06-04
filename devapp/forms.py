from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError

from djing.lib.tln.tln import ValidationError as TlnValidationError
from . import models
from djing import MAC_ADDR_REGEX, IP_ADDR_REGEX


class DeviceForm(forms.ModelForm):
    mac_addr = forms.CharField(widget=forms.TextInput(attrs={
        'pattern': MAC_ADDR_REGEX,
        'required': True
    }), error_messages={
        'required': _('Mac address is required for fill'),
        'unique': _('Device with that mac is already exist')
    })

    def clean_snmp_extra(self):
        snmp_extra = self.cleaned_data.get('snmp_extra')
        if snmp_extra is None:
            return
        device = self.instance
        manager = device.get_manager_object()
        try:
            manager.validate_extra_snmp_info(snmp_extra)
        except TlnValidationError as e:
            raise ValidationError(
                e, code='invalid'
            )
        return snmp_extra

    class Meta:
        model = models.Device
        exclude = ('map_dot', 'status')
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'pattern': IP_ADDR_REGEX,
                'placeholder': '192.168.0.100'
            }),
            'comment': forms.TextInput(attrs={
                'required': True
            })
        }


class PortForm(forms.ModelForm):
    class Meta:
        model = models.Port
        exclude = ['device']
        widgets = {
            'num': forms.NumberInput(attrs={
                'min': '0'
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
