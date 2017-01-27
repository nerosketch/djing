# -*- coding: utf-8 -*-
from django import forms
from .models import Dot


class DotForm(forms.ModelForm):
    class Meta:
        model = Dot
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': '', 'autofocus':''}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'required': ''}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'required': ''})
        }
