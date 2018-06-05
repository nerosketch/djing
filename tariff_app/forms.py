from django import forms

from . import models


class TariffForm(forms.ModelForm):
    class Meta:
        model = models.Tariff
        fields = '__all__'


class PeriodicPayForm(forms.ModelForm):
    class Meta:
        model = models.PeriodicPay
        exclude = ('when_add', 'extra_info')
