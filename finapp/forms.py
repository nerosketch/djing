from django import forms
from finapp.models import PayAllTimeGateway


class PayAllTimeGatewayForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance')
        if instance and instance.pk:
            self.fields['slug'].disabled = True

    def clean_slug(self):
        if self.instance and self.instance.pk:
            return self.instance.slug
        return self.data['slug']

    class Meta:
        model = PayAllTimeGateway
        fields = '__all__'
