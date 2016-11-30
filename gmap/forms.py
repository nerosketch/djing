from django import forms

from gmap.models import MapMarker, CountryISOCode


class ModifiedChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if 'long_name' in obj:
            return obj['long_name']

        if 'state' in obj:
            return obj['state']

        return 'No Data'


class MapSearchForm(forms.Form):
    state = ModifiedChoiceField(
        queryset=MapMarker.objects.filter(country__iso_3='USA').values('state').order_by('state').distinct(), label='')
    country = ModifiedChoiceField(queryset=CountryISOCode.objects.order_by('long_name').values('long_name'), label='')
