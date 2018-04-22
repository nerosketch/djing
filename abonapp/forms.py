from datetime import datetime
from django.utils.translation import ugettext as _
from django import forms
from django.contrib.auth.hashers import make_password
from random import choice
from string import digits, ascii_lowercase
from . import models
from django.conf import settings
from djing import IP_ADDR_REGEX

TELEPHONE_REGEXP = getattr(settings, 'TELEPHONE_REGEXP', r'^\+[7,8,9,3]\d{10,11}$')


def generate_random_chars(length=6, chars=digits, split=2, delimiter=''):
    username = ''.join([choice(chars) for i in range(length)])

    if split:
        username = delimiter.join([username[start:start + split] for start in range(0, len(username), split)])

    try:
        models.Abon.objects.get(username=username)
        return generate_random_username(length=length, chars=chars, split=split, delimiter=delimiter)
    except models.Abon.DoesNotExist:
        return username


def generate_random_username():
    username = generate_random_chars(length=6, chars=digits)
    return str(int(username))


def generate_random_password():
    return generate_random_chars(length=8, chars=digits + ascii_lowercase)


class AbonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AbonForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance')
        if instance is not None and instance.group is not None:
            abon_group_queryset = models.AbonStreet.objects.filter(group=instance.group)
        elif 'group' in self.initial.keys() and self.initial['group'] is not None:
            abon_group_queryset = models.AbonStreet.objects.filter(group=self.initial['group'])
        else:
            abon_group_queryset = None
        if abon_group_queryset is not None:
            self.fields['street'].queryset = abon_group_queryset
        if instance is not None and instance.is_dynamic_ip:
            self.fields['ip_address'].widget.attrs['readonly'] = True

    username = forms.CharField(max_length=127, required=False, initial=generate_random_username,
                               widget=forms.TextInput(attrs={
                                   'placeholder': _('login'),
                                   'required': '',
                                   'pattern': r'^\w{1,127}$'
                               }))

    password = forms.CharField(max_length=64, initial=generate_random_password, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'password', 'autocomplete': 'new-password'
    }))

    ip_address = forms.CharField(widget=forms.TextInput(attrs={
        'pattern': IP_ADDR_REGEX
    }), label=_('Ip Address'))

    class Meta:
        model = models.Abon
        fields = ['username', 'telephone', 'fio', 'group', 'description', 'street', 'house', 'is_active', 'ip_address']
        widgets = {
            'fio': forms.TextInput(attrs={
                'placeholder': _('fio'),
                'required': ''
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': _('telephone placeholder'),
                'pattern': TELEPHONE_REGEXP,
                'required': '',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={'rows': '4'}),
            'is_active': forms.NullBooleanSelect(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        raw_password = self.cleaned_data['password']
        acc = super(AbonForm, self).save(commit=False)
        acc.password = make_password(raw_password)
        if commit:
            acc.save()
        try:
            abon_raw_passw = models.AbonRawPassword.objects.get(account=acc)
            abon_raw_passw.passw_text = raw_password
            abon_raw_passw.save(update_fields=['passw_text'])
        except models.AbonRawPassword.DoesNotExist:
            models.AbonRawPassword.objects.create(
                account=acc,
                passw_text=raw_password
            )
        return acc


class PassportForm(forms.ModelForm):
    class Meta:
        model = models.PassportInfo
        exclude = ['abon']
        widgets = {
            'series': forms.TextInput(attrs={'required': '', 'pattern': '^\d{4}$'}),
            'number': forms.TextInput(attrs={'required': '', 'pattern': '^\d{6}$'}),
            'distributor': forms.TextInput(attrs={'required': ''}),
            'date_of_acceptance': forms.DateInput(attrs={'class': 'form-control', 'required': ''})
        }
        initials = {
            'date_of_acceptance': datetime(year=2014, month=6, day=1)
        }


class ExtraFieldForm(forms.ModelForm):
    class Meta:
        model = models.ExtraFieldsModel
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.TextInput(attrs={'class': 'form-control'})
        }


class AbonStreetForm(forms.ModelForm):
    class Meta:
        model = models.AbonStreet
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': '', 'autofocus': ''}),
            'group': forms.Select(attrs={'class': 'form-control'})
        }


class AdditionalTelephoneForm(forms.ModelForm):
    class Meta:
        model = models.AdditionalTelephone
        exclude = ['abon']
        widgets = {
            'telephone': forms.TextInput(attrs={
                'placeholder': _('telephone placeholder'),
                'pattern': TELEPHONE_REGEXP,
                'required': '',
                'class': 'form-control'
            }),
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'required': ''})
        }


class PeriodicPayForIdForm(forms.ModelForm):
    class Meta:
        model = models.PeriodicPayForId
        exclude = ['account']


class ExportUsersForm(forms.Form):
    FIELDS_CHOICES = (
        ('username', _('profile username')),
        ('fio', _('fio')),
        ('ip_address', _('Ip Address')),
        ('description', _('Comment')),
        ('street__name', _('Street')),
        ('house', _('House')),
        ('birth_day', _('birth day')),
        ('is_active', _('Is active')),
        ('telephone', _('Telephone')),
        ('current_tariff__tariff__title', _('Service title')),
        ('ballance', _('Ballance')),
        ('device__comment', _('Device')),
        ('dev_port__descr', _('Device port')),
        ('is_dynamic_ip', _('Is dynamic ip'))
    )
    fields = forms.MultipleChoiceField(choices=FIELDS_CHOICES,
                                       widget=forms.CheckboxSelectMultiple(attrs={"checked": ""}),
                                       label=_('Fields'))


class MarkersForm(forms.ModelForm):
    class Meta:
        model = models.Abon
        fields = ['markers']

    def save(self, commit=True):
        instance = super(MarkersForm, self).save(commit=False)
        return instance.save(update_fields=['markers'])
