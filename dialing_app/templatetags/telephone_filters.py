import re
from django import template
from django.shortcuts import resolve_url
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def abon_if_telephone(value):
    """Возвращаем ссыль на абонента если передали номер телефона"""
    if re.match(r'^\+?\d+$', value):
        if value[0] != '+':
            value = '+' + value
        url = resolve_url('dialapp:to_abon', tel=value)
        a = '<a href="%s">%s</a>' % (url, value)
        return a
    else:
        return value
