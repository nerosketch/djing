from django import template
from django.shortcuts import resolve_url

from ip_pool.models import NetworkModel

register = template.Library()


@register.simple_tag
def get_device_kinds():
    return ((
        resolve_url('ip_pool:networks_%s' % kind_code),
        kind_descr
    )for kind_code, kind_descr in NetworkModel.NETWORK_KINDS)
