from urllib.parse import unquote

from django import template
from django.conf import settings
from django.utils.http import is_safe_url

register = template.Library()


@register.simple_tag
def global_var(var_name):
    return getattr(settings, var_name, '')


@register.simple_tag
def back_url(request):
    url = request.META.get('HTTP_REFERER')
    if url:
        url = unquote(url)  # HTTP_REFERER may be encoded.
    if not is_safe_url(url=url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        url = '/'
    return url
