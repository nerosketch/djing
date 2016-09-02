# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django import forms
from models import TASK_PRIORITIES
from accounts_app.models import UserProfile
from devapp.models import Device


class TaskFrm(forms.Form):
    descr = forms.CharField(max_length=128, required=True, widget=forms.TextInput(attrs={
        'placeholder': u'Краткое описание',
        'class': "form-control",
        'id': "descr",
        'required':''
    }))
    recipient = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'recipient', 'required':''})
    )
    device = forms.ModelChoiceField(
        queryset=Device.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'device', 'required':''})
    )
    priority = forms.ChoiceField(
        choices=TASK_PRIORITIES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'priority'}),
        required=False,
        initial=TASK_PRIORITIES[2][0]
    )
    out_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'id': 'out_date'}),
        initial=datetime.now()+timedelta(days=7)
    )
