from ipaddress import ip_network
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.fields import CharField


def validate_ipv46_address_with_subnet(v: str):
    try:
        ip = ip_network(v)
        return str(ip)
    except ValueError as e:
        raise ValidationError(e)


class GenericIPAddressFormField(CharField):

    def __init__(self, unpack_ipv4=False, *args, **kwargs):
        self.unpack_ipv4 = unpack_ipv4
        self.default_validators = validate_ipv46_address_with_subnet,
        del kwargs['protocol']
        super(GenericIPAddressFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return ''
        value = value.strip()
        if value and ':' in value:
            ip = ip_network(value, strict=False)
            return ip.compressed
        return value


class GenericIpAddressWithPrefix(models.GenericIPAddressField):
    description = _("IP address with prefix length, or subnet for ipv4")

    def __init__(self, prefix=None, *args, **kwargs):
        self.prefix = prefix
        super(GenericIpAddressWithPrefix, self).__init__(*args, **kwargs)
        self.default_error_messages['invalid'] = _('Enter a valid IPv4 or IPv6 address with prefix length.')
        self.max_length = 43

    def deconstruct(self):
        name, path, args, kwargs = super(GenericIpAddressWithPrefix, self).deconstruct()
        if kwargs.get("max_length") == 43:
            del kwargs['max_length']
        return name, path, args, kwargs

    @property
    def validators(self):
        return validate_ipv46_address_with_subnet,

    def to_python(self, value):
        if value is None:
            return None
        value = value.strip()
        if ':' in value:
            ip = ip_network(value)
            return ip.with_prefixlen
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)
        return connection.ops.adapt_ipaddressfield_value(value)

    def get_prep_value(self, value):
        value = super(GenericIpAddressWithPrefix, self).get_prep_value(value)
        if value is None:
            return None
        if value and ':' in value:
            try:
                return ip_network(value)
            except ValidationError:
                pass
        return value

    def formfield(self, **kwargs):
        defaults = {
            'protocol': self.protocol,
            'form_class': GenericIPAddressFormField,
        }
        defaults.update(kwargs)
        return super(GenericIpAddressWithPrefix, self).formfield(**defaults)
