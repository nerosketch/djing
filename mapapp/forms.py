# -*- coding: utf-8 -*-
from django import forms
from .models import Dot


class DotForm(forms.ModelForm):
    class Meta:
        model = Dot
        exclude = ('devices',)

        widgets = {
            'title': forms.TextInput(attrs={'required': '', 'autofocus': ''}),
        }
