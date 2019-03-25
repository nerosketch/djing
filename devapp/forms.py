from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError

from djing.lib import DuplicateEntry
from devapp.expect_scripts import ExpectValidationError
from . import models
from djing import MAC_ADDR_REGEX, IP_ADDR_REGEX


class DeviceForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """
        Move comment from value to placeholder in HTML form
        """
        initial = kwargs.get('initial')
        if initial:
            comment = initial.get('comment')
            del initial['comment']
        else:
            comment = None
        super(DeviceForm, self).__init__(*args, **kwargs)
        if comment:
            self.fields['comment'].widget.attrs['placeholder'] = comment

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
        # fixme: if creating device than check disabled
        if device.pk is not None:
            manager_class = device.get_manager_klass()
            try:
                manager_class.validate_extra_snmp_info(snmp_extra)
            except ExpectValidationError as e:
                raise ValidationError(
                    e, code='invalid'
                )
        return snmp_extra

    class Meta:
        model = models.Device
        exclude = ('map_dot', 'status', 'extra_data')
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'pattern': IP_ADDR_REGEX,
                'placeholder': '192.168.0.100'
            }),
            'comment': forms.TextInput(attrs={
                'required': True
            })
        }


class DeviceExtraDataForm(forms.ModelForm):
    class Meta:
        model = models.Device
        fields = ('extra_data',)


class PortForm(forms.ModelForm):
    class Meta:
        model = models.Port
        exclude = ('device',)
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
                raise DuplicateEntry(_('Port number on device must be unique'))
            else:
                raise models.DeviceDBException(e)


class DeviceRebootForm(forms.Form):
    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    is_save = forms.BooleanField(label=_('Is save before reboot'), required=False)
