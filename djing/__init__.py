import importlib
from netaddr import mac_unix, mac_eui48


MAC_ADDR_REGEX = r'^([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2})$'

IP_ADDR_REGEX = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' \
                r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'


class mac_linux(mac_unix):
    """MAC format with zero-padded all upper-case hex and colon separated"""
    word_fmt = '%x'


def default_dialect():
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
VERSION = __version__   # synonym
default_app_config = 'abonapp.apps.AbonappConfig'
