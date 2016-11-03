# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django import forms

from models import TASK_PRIORITIES, TASK_STATES
from accounts_app.models import UserProfile
from devapp.models import Device


class TaskFrm(forms.Form):
    descr = forms.CharField(max_length=128, required=True, widget=forms.TextInput(attrs={
        'placeholder': u'Краткое описание',
        'class': "form-control",
        'required':''
    }))
    recipient = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required':''})
    )
    device = forms.ModelChoiceField(
        queryset=Device.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'required':''})
    )
    priority = forms.ChoiceField(
        choices=TASK_PRIORITIES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        initial=TASK_PRIORITIES[2][0]
    )
    state = forms.ChoiceField(
        choices=TASK_STATES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        initial=TASK_PRIORITIES[0][0]
    )
    out_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control',}),
        initial=datetime.now()+timedelta(days=7)
    )
