from functools import wraps
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import redirect

from djing.lib import check_sign

DEBUG = getattr(settings, 'DEBUG', False)
API_AUTH_SECRET = getattr(settings, 'API_AUTH_SECRET')


def require_ssl(view):
    """
    Decorator that requires an SSL connection. If the current connection is not SSL, we redirect to the SSL version of
    the page.
    from: https://gist.github.com/ckinsey/9709984
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not DEBUG and not request.is_secure():
            target_url = "https://" + request.META['HTTP_HOST'] + request.path_info
            return HttpResponseRedirect(target_url)
        return view(request, *args, **kwargs)

    return wrapper


# Allow to view only admins
def only_admins(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        if request.user.is_admin:
            return fn(request, *args, **kwargs)
        else:
            return redirect('client_side:home')
    return wrapped


# hash auth for functional views
def hash_auth_view(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        sign = request.GET.get('sign')
        if sign is None or sign == '':
            return HttpResponseForbidden('Access Denied')

        # Transmittent get list without sign
        get_values = request.GET.copy()
        del get_values['sign']
        values_list = [l for l in get_values.values() if l]
        values_list.sort()
        values_list.append(API_AUTH_SECRET)
        if check_sign(values_list, sign):
            return fn(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Access Denied')
    return wrapped


class abstract_static_method(staticmethod):
    __slots__ = ()

    def __init__(self, func):
        super(abstract_static_method, self).__init__(func)
        func.__isabstractmethod__ = True

    __isabstractmethod__ = True
