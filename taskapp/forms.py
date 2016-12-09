# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django import forms
from models import Task
from accounts_app.models import UserProfile


class TaskFrm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_admin=True),
        widget=forms.Select(attrs={'class': 'form-control', 'required':''})
    )

    class Meta:
        model = Task
        exclude = ['time_of_create', 'author']
        widgets = {
            'descr': forms.TextInput(attrs={
                'placeholder': u'Краткое описание',
                'class': "form-control",
                'required': ''
            }),
            'device': forms.Select(attrs={'class': 'form-control', 'required':''}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'out_date': forms.DateInput(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
            'abon': forms.Select(attrs={'class': 'form-control'})
        }
        initials = {
            'out_date': datetime.now()+timedelta(days=3)
        }
