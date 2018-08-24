from ipaddress import ip_address, AddressValueError

from django import template
from django.db.models import Model
from django.apps import apps
from ip_pool.models import IpLeaseModel
from six import string_types, class_types

register = template.Library()


@register.simple_tag
def klass_name(klass):
    if type(klass) is class_types and issubclass(klass, Model):
        kl = klass
    elif isinstance(klass, string_types):
        app_label, model_name = klass.split('.', 1)
        kl = apps.get_model(app_label, model_name)
    else:
        return 'Type not detected'
    return kl._meta.verbose_name


@register.simple_tag
def can_login_by_location(request):
    try:
        remote_ip = ip_address(request.META.get('REMOTE_ADDR'))
        if remote_ip.version == 4:
            has_leases = IpLeaseModel.objects.filter(ip=str(remote_ip)).exists()
            return has_leases
    except AddressValueError:
        pass
    return False
