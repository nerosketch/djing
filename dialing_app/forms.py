from django import forms
from .models import SMSOut


class SMSOutForm(forms.ModelForm):
    class Meta:
        model = SMSOut
        fields = ['dst', 'text']
