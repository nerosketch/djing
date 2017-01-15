# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django import forms
from models import Task


class TaskFrm(forms.ModelForm):

    class Meta:
        model = Task
        exclude = ['time_of_create', 'author', 'recipients', 'device']
        widgets = {
            'descr': forms.TextInput(attrs={
                'placeholder': u'Краткое описание',
                'class': "form-control",
                'autofocus': ''
            }),
            #'device': forms.Select(attrs={'class': 'form-control', 'required':''}),
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
