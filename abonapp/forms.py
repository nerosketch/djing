# -*- coding: utf-8 -*-
from django import forms
from random import choice
from string import digits
from . import models


def generate_random_username(length=6, chars=digits, split=2, delimiter=''):
    username = ''.join([choice(chars) for i in range(length)])

    if split:
        username = delimiter.join([username[start:start+split] for start in range(0, len(username), split)])

    try:
        models.Abon.objects.get(username=username)
        return generate_random_username(length=length, chars=chars, split=split, delimiter=delimiter)
    except models.Abon.DoesNotExist:
        return username


class AbonForm(forms.ModelForm):
    username = forms.CharField(max_length=127, required=False, initial=generate_random_username, widget=forms.TextInput(attrs={
        'placeholder': 'Логин',
        'class': "form-control",
        'required':''
    }))

    class Meta:
        model = models.Abon
        fields = ['username', 'telephone', 'fio', 'group', 'description', 'street', 'house', 'is_active']
        widgets = {
            'fio': forms.TextInput(attrs={
                'placeholder': 'ФИО',
                'class': "form-control",
                'required': ''
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': '+[7,8,9,3] и 10,11 цифр',
                'pattern': r'^\+[7,8,9,3]\d{10,11}$',
                'required': '',
                'class': 'form-control'
            }),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows':'3', 'cols':'65'}),
            'street': forms.Select(attrs={'class': 'form-control'}),
            'house': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.NullBooleanSelect(attrs={'class': 'form-control'})
        }


class AbonGroupForm(forms.ModelForm):
    class Meta:
        model = models.AbonGroup
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'profiles': forms.TextInput(attrs={'class': 'form-control'})
        }


class BuyTariff(forms.Form):
    tariff = forms.ModelChoiceField(
        queryset=models.Tariff.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
