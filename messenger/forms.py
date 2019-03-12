from django import forms
from messenger import models


class MessengerForm(forms.ModelForm):
    class Meta:
        model = models.Messenger
        fields = ('bot_type',)


class MessengerViberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['initial']['bot_type'] = 1
        super().__init__(*args, **kwargs)
        inst = getattr(self, 'instance')
        if inst:
            self.fields['bot_type'].disabled = True
            #self.fields['bot_type'].widget.attrs['disabled'] = True

    class Meta:
        model = models.ViberMessenger
        fields = '__all__'


class MessengerViberMessageForm(forms.ModelForm):
    class Meta:
        model = models.ViberMessage
        fields = '__all__'
