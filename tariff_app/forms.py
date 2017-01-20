from django import forms

from . import models


class TariffForm(forms.ModelForm):
    class Meta:
        model = models.Tariff
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'descr': forms.TextInput(attrs={'class': 'form-control'}),
            'speedIn': forms.NumberInput(attrs={'class': 'form-control'}),
            'speedOut': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_of_action': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'calc_type': forms.Select(attrs={'class': 'form-control'})
        }
