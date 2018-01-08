from django.forms import CharField
from django.forms.widgets import TextInput
from django.core.validators import RegexValidator, _lazy_re_compile
from django.forms.fields import EMPTY_VALUES
from django.forms.utils import ValidationError
from django.utils.translation import gettext_lazy as _
from netaddr import EUI, AddrFormatError
from . import MAC_ADDR_REGEX


mac_address_validator = RegexValidator(
    _lazy_re_compile(MAC_ADDR_REGEX),
    message=_('Enter a valid integer.'),
    code='invalid',
)


class MACAddressField(CharField):
    widget = TextInput
    default_validators = [mac_address_validator]
    default_error_messages = {
        'invalid': _('Enter a valid MAC Address.'),
    }

    def clean(self, value):
        """
        Validates that EUI() can be called on the input. Returns the result
        of EUI(). Returns None for empty values.
        """
        value = super(MACAddressField, self).clean(value)
        if value in EMPTY_VALUES:
            return None
        try:
            value = EUI(str(value), version=48)
        except (ValueError, TypeError, AddrFormatError):
            raise ValidationError(self.error_messages['invalid'])
        return value
