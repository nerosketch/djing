import os
import re
import importlib
import typing as t
from urllib.parse import unquote

from django.http import HttpResponseRedirect, HttpResponse
from netaddr import mac_unix, mac_eui48

from django.shortcuts import _get_queryset
from django.utils.http import is_safe_url

MAC_ADDR_REGEX = '^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$'

IP_ADDR_REGEX = (
    '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)


class mac_linux(mac_unix):
    """MAC format with zero-padded all upper-case hex and colon separated"""
    word_fmt = '%x'


def default_dialect(*args):
    return mac_linux


def format_mac(eui_obj, dialect):
    # Format a EUI instance as a string using the supplied dialect class, allowing custom string classes by
    # passing directly or as a string, a la 'module.dialect_cls', where 'module' is the module and 'dialect_cls'
    # is the class name of the custom dialect. The dialect must either be defined or imported by the module's __init__.py if
    # the module is a package.
    if not isinstance(dialect, mac_eui48):
        if isinstance(dialect, str):
            module, dialect_cls = dialect.split('.')
            dialect = getattr(importlib.import_module(module), dialect_cls)
    eui_obj.dialect = dialect
    return str(eui_obj)


from pkg_resources import get_distribution, DistributionNotFound

try:
    _dist = get_distribution('django-macaddress')
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version
VERSION = __version__  # synonym
default_app_config = 'abonapp.apps.AbonappConfig'


def ping(ip_addr: str, count=1):
    if re.match(IP_ADDR_REGEX, ip_addr):
        response = os.system("`which ping` -4Anq -c%d -W1 %s > /dev/null" % (count, ip_addr))
        return True if response == 0 else False
    else:
        return False


def get_object_or_None(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except AttributeError:
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_404() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    except queryset.model.DoesNotExist:
        return


# Type for all objects who can convertable to json
_JSONType_0 = t.Union[str, int, float, bool, None, t.Dict[str, t.Any], t.List[t.Any]]
_JSONType_1 = t.Union[str, int, float, bool, None, t.Dict[str, _JSONType_0], t.List[_JSONType_0]]
_JSONType_2 = t.Union[str, int, float, bool, None, t.Dict[str, _JSONType_1], t.List[_JSONType_1]]
_JSONType_3 = t.Union[str, int, float, bool, None, t.Dict[str, _JSONType_2], t.List[_JSONType_2]]
JSONType = t.Union[str, int, float, bool, None, t.Dict[str, _JSONType_3], t.List[_JSONType_3]]


def httpresponse_to_referrer(request):
    next = request.META.get('HTTP_REFERER')
    if next:
        next = unquote(next)
    if not is_safe_url(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next = '/'
    return HttpResponseRedirect(next) if next else HttpResponse(status=204)
