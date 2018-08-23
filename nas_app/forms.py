from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from nas_app.models import NASModel
from djing import IP_ADDR_REGEX


class NasForm(forms.ModelForm):

    def clean_default(self):
        cd = self.cleaned_data
        default = cd.get('default')
        if default:
            try:
                if self.instance:
                    NASModel.objects.filter(default=True).exclude(pk=self.instance.pk).get()
                else:
                    NASModel.objects.get(default=True).exclude(pk=1).get()
                raise ValidationError(message=_('Can be only one default gateway'), code='unique')
            except NASModel.DoesNotExist:
                pass
        return default

    class Meta:
        model = NASModel
        fields = '__all__'
        widgets = {
            'ip_address': forms.TextInput(attrs={
                'pattern': IP_ADDR_REGEX
            })
        }
