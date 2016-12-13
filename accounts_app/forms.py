# -*- coding: utf-8 -*-
from django import forms
from models import UserProfile


class SetupPerms(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user_permissions']
        widgets = {
            'user_permissions': forms.CheckboxSelectMultiple()
        }
