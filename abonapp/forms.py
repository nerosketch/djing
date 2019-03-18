from django.utils.translation import ugettext as _
from django import forms
from django.contrib.auth.hashers import make_password
from random import choice
from string import digits, ascii_lowercase

from djing.lib import LogicError
from ip_pool.models import NetworkModel
from gw_app.models import NASModel
from abonapp import models
from django.conf import settings


def _generate_random_chars(length=6, chars=digits, split=2, delimiter=''):
    username = ''.join(choice(chars) for i in range(length))

    if split:
        username = delimiter.join(
            username[start:start + split]
            for start in range(0, len(username), split)
        )

    try:
        models.Abon.objects.get(username=username)
        return _generate_random_chars(
            length=length, chars=chars,
            split=split, delimiter=delimiter
        )
    except models.Abon.DoesNotExist:
        return username


def _generate_random_username():
    username = _generate_random_chars(length=6, chars=digits)
    return str(int(username))


def _generate_random_password():
    return _generate_random_chars(length=8, chars=digits + ascii_lowercase)


class AbonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AbonForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance')
        if instance is not None and instance.group is not None:
            abon_group_queryset = models.AbonStreet.objects.filter(
                group=instance.group
            )
        elif 'group' in self.initial.keys() and self.initial['group'] is not None:
            abon_group_queryset = models.AbonStreet.objects.filter(
                group=self.initial['group']
            )
        else:
            abon_group_queryset = None
        if abon_group_queryset is not None:
            self.fields['street'].queryset = abon_group_queryset
        if instance.pk is None:
            self.initial['nas'] = NASModel.objects.filter(default=True).first()

    username = forms.CharField(max_length=127, required=False,
                               initial=_generate_random_username,
                               widget=forms.TextInput(attrs={
                                   'placeholder': _('login'),
                                   'required': '',
                                   'pattern': r'^\w{1,127}$'
                               }), label=_('login'))

    password = forms.CharField(
        max_length=64, initial=_generate_random_password,
        widget=forms.TextInput(attrs={
            'type': 'password', 'autocomplete': 'new-password'
        }),
        label=_('Password')
    )

    class Meta:
        model = models.Abon
        fields = ('username', 'telephone', 'fio', 'group',
                  'description', 'street', 'house', 'is_active', 'nas')
        widgets = {
            'fio': forms.TextInput(attrs={
                'placeholder': _('fio'),
                'required': ''
            }),
            'telephone': forms.TextInput(attrs={
                'placeholder': _('telephone placeholder'),
                'pattern': getattr(
                    settings, 'TELEPHONE_REGEXP',
                    r'^(\+[7,8,9,3]\d{10,11})?$'
                )
            }),
            'description': forms.Textarea(attrs={'rows': '4'})
        }

    def save(self, commit=True):
        raw_password = self.cleaned_data['password']
        acc = super(AbonForm, self).save(commit=False)
        acc.password = make_password(raw_password)
        if commit:
            acc.save()
        try:
            abon_raw_passw = models.AbonRawPassword.objects.get(account=acc)
            abon_raw_passw.passw_text = raw_password
            abon_raw_passw.save(update_fields=('passw_text',))
        except models.AbonRawPassword.DoesNotExist:
            models.AbonRawPassword.objects.create(
                account=acc,
                passw_text=raw_password
            )
        return acc


class PassportForm(forms.ModelForm):
    class Meta:
        model = models.PassportInfo
        exclude = ('abon',)
        widgets = {
            'series': forms.TextInput(attrs={
                'required': '',
                'pattern': '^\d{4}$'}
            ),
            'number': forms.TextInput(
                attrs={'required': '', 'pattern': '^\d{6}$'}
            ),
            'distributor': forms.TextInput(attrs={'required': ''}),
            'date_of_acceptance': forms.DateInput(attrs={
                'class': 'form-control', 'required': ''
            }, format='%Y-%m-%d')
        }


class AbonStreetForm(forms.ModelForm):
    class Meta:
        model = models.AbonStreet
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': '', 'autofocus': ''
            }),
            'group': forms.Select(attrs={'class': 'form-control'})
        }


class AdditionalTelephoneForm(forms.ModelForm):
    class Meta:
        model = models.AdditionalTelephone
        exclude = ('abon',)
        widgets = {
            'telephone': forms.TextInput(attrs={
                'placeholder': _('telephone placeholder'),
                'pattern': getattr(
                    settings, 'TELEPHONE_REGEXP',
                    r'^(\+[7,8,9,3]\d{10,11})?$'
                ),
                'required': '',
                'class': 'form-control'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control', 'required': ''
            })
        }


class PeriodicPayForIdForm(forms.ModelForm):
    class Meta:
        model = models.PeriodicPayForId
        exclude = ('account',)
        widgets = {
            'next_pay': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }


class ExportUsersForm(forms.Form):
    FIELDS_CHOICES = (
        ('username', _('profile username')),
        ('fio', _('fio')),
        ('description', _('Comment')),
        ('street__name', _('Street')),
        ('house', _('House')),
        ('birth_day', _('birth day')),
        ('is_active', _('Is active')),
        ('telephone', _('Telephone')),
        ('current_tariff__tariff__title', _('Service title')),
        ('ballance', _('Balance')),
        ('device__comment', _('Device')),
        ('dev_port__descr', _('Device port')),
        ('is_dynamic_ip', _('Is dynamic ip'))
    )
    fields = forms.MultipleChoiceField(
        choices=FIELDS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"checked": ""}),
        label=_('Fields')
    )


class MarkersForm(forms.ModelForm):
    class Meta:
        model = models.Abon
        fields = 'markers',

    def save(self, commit=True):
        instance = super(MarkersForm, self).save(commit=False)
        instance.save(update_fields=('markers',))
        return instance


class AmountMoneyForm(forms.Form):
    amount = forms.FloatField(max_value=5000, label=_('Amount of money'))
    comment = forms.CharField(
        max_length=128, label=_('Comment'),
        required=False
    )


class AddIpForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance')
        if instance:
            if instance.group:
                self.fields['networks'].queryset = NetworkModel.objects.filter(
                    groups=instance.group
                )
        if not self.initial['ip_address']:
            if instance:
                net = NetworkModel.objects.filter(
                    groups=instance.group
                ).first()
                if net is not None:
                    ips = (ip.ip_address for ip in
                           models.Abon.objects.filter(
                               group__in=net.groups.all(),
                               nas=instance.nas
                           ).order_by('ip_address').only(
                               'ip_address').iterator())
                    free_ip = net.get_free_ip(ips)
                    self.initial['ip_address'] = free_ip
            else:
                raise LogicError(_('Subnet has not attached to current group'))

    networks = forms.ModelChoiceField(
        label=_('Networks'),
        queryset=NetworkModel.objects.none(),
        empty_label=None
    )

    class Meta:
        model = models.Abon
        fields = 'ip_address',
