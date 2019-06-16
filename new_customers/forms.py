from django import forms
from new_customers.models import PotentialSubscriber


class CustomerModelForm(forms.ModelForm):
    class Meta:
        model = PotentialSubscriber
        exclude = ('make_data',)
