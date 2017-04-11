# -*- coding: utf-8 -*-
from datetime import datetime
from django.utils.translation import ugettext as _
from django import forms
from django.contrib.auth.hashers import make_password
from random import choice
from string import digits, ascii_lowercase
from . import models
from .formfields import MACAddressField


def generate_random_username(length=6, chars=digits, split=2, delimiter=''):
    username = ''.join([choice(chars) for i in range(length)])

    if split:
        username = delimiter.join([username[start:start+split] for start in range(0, len(username), split)])

    try:
        models.Abon.objects.get(username=username)
        return generate_random_username(length=length, chars=chars, split=split, delimiter=delimiter)
    except models.Abon.DoesNotExist:
        return username


def generate_random_password():
    return generate_random_username(length=8, chars=digits+ascii_lowercase)


class AbonForm(forms.ModelForm):
    username = forms.CharField(max_length=127, required=False, initial=generate_random_username, widget=forms.TextInput(attrs={
        'placeholder': _('login'),
        'class': "form-control",
        'required': ''
    }))

    password = forms.CharField(max_length=64, initial=generate_random_password,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'password', 'autocomplete': 'new-password'}))

    class Meta:
        model = models.Abon
        fields = ['username', 'telephone', 'fio', 'group', 'description', 'street', 'house', 'is_active']
        widgets = {
            'fio': forms.TextInput(attrs={
                'placeholder': _('fio'),
                'class': "form-control",
                'required': ''
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': _('telephone placeholder'),
                'pattern': r'^\+[7,8,9,3]\d{10,11}$',
                'required': '',
                'class': 'form-control'
            }),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '4'}),
            'street': forms.Select(attrs={'class': 'form-control'}),
            'house': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.NullBooleanSelect(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        raw_password = self.cleaned_data['password']
        acc = super().save(commit=False)
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


class Opt82Form(forms.ModelForm):
    mac = MACAddressField(widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': r'^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$', 'required': ''}))
    class Meta:
        model = models.Opt82
        fields = '__all__'
        widgets = {
            'port': forms.NumberInput(attrs={'class': 'form-control', 'required': ''})
        }

    #def save(self, commit=True):
    #    super().save(commit=commit)


class AbonGroupForm(forms.ModelForm):
    class Meta:
        model = models.AbonGroup
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'profiles': forms.TextInput(attrs={'class': 'form-control'})
        }


class PassportForm(forms.ModelForm):
    class Meta:
        model = models.PassportInfo
        exclude = ['abon']
        widgets = {
            'series': forms.TextInput(attrs={'class': 'form-control', 'required': '', 'pattern': '^\d{4}$'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'required': '', 'pattern': '^\d{6}$'}),
            'distributor': forms.TextInput(attrs={'class': 'form-control', 'required': ''}),
            'date_of_acceptance': forms.DateInput(attrs={'class': 'form-control', 'required': ''})
        }
        initials = {
            'date_of_acceptance': datetime(year=2014, month=6, day=1)
        }
