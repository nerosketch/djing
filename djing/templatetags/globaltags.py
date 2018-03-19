from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def global_var(var_name):
    return getattr(settings, var_name, '')
