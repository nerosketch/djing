# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import RegexValidator

from . import models
from mydefs import ip_addr_regex


class AbonForm(forms.Form):
    username = forms.CharField(max_length=127, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Логин',
        'class': "form-control",
        'id': "login"
    }))
    fio = forms.CharField(max_length=256, widget=forms.TextInput(attrs={
        'placeholder': 'ФИО',
        'class': "form-control",
        'id': "fio"
    }), required=False)
    ip_address = forms.GenericIPAddressField(protocol='ipv4', required=False, widget=forms.TextInput(attrs={
        'pattern': ip_addr_regex,
        'placeholder': '127.0.0.1',
        'class': "form-control",
        'id': "ip"
    }))

    telephone = forms.CharField(
        max_length=16,
        validators=[RegexValidator(r'^\+[7,8,9,3]\d{10,11}$')],
        widget=forms.TextInput(attrs={
            'placeholder': '+[7,8,9,3] и 10,11 цифр',
            'pattern': r'^\+[7,8,9,3]\d{10,11}$',
            'required': '',
            'class': 'form-control',
            'id': 'telephone'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.NullBooleanSelect(attrs={'class': 'form-control', 'id': 'isactive'})
    )

    group = forms.ModelChoiceField(
        queryset=models.AbonGroup.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'grp'})
    )
    address = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'address'})
    )


class AbonGroupForm(forms.ModelForm):
    class Meta:
        model = models.AbonGroup
        fields = '__all__'
        widgets = {
            'class': 'form-control'
        }


class BuyTariff(forms.Form):
    tariff = forms.ModelChoiceField(
        queryset=models.Tariff.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'tariff'})
    )
