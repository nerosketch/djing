from functools import wraps
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect

from djing.lib import check_sign


def require_ssl(view):
    """
    Decorator that requires an SSL connection. If the current connection is not SSL, we redirect to the SSL version of
    the page.
    from: https://gist.github.com/ckinsey/9709984
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        debug = getattr(settings, 'DEBUG', False)
        if not debug and not request.is_secure():
            target_url = "https://%s%s" % (request.META['HTTP_HOST'], request.path_info)
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
        api_auth_secret = getattr(settings, 'API_AUTH_SECRET')
        sign = request.GET.get('sign')
        if sign is None or sign == '':
            return HttpResponseForbidden('Access Denied')

        # Transmittent get list without sign
        get_values = request.GET.copy()
        del get_values['sign']
        values_list = [l for l in get_values.values() if l]
        values_list.sort()
        values_list.append(api_auth_secret)
        if check_sign(values_list, sign):
            return fn(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Access Denied')
    return wrapped


# Lazy initialize metaclass
class LazyInitMetaclass(type):
    """
    Type this metaclass if you want to make your object with lazy initialize.
    Method __init__ called only when you try to call something method
    from object of your class.
    """
    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        new_class_new = super(LazyInitMetaclass, mcs).__new__

        def _lazy_call_decorator(fn):
            def wrapped(self, *args, **kwargs):
                if not self._is_initialized:
                    self._lazy_init(*self._args, **self._kwargs)
                return fn(self, *args, **kwargs)

            return wrapped

        # Apply decorator to all public class methods
        new_attrs = {k: _lazy_call_decorator(v) for k, v in attrs.items() if not k.startswith('__') and not k.endswith('__') and callable(v)}
        if new_attrs:
            attrs.update(new_attrs)
        attrs['_is_initialized'] = False

        new_class = new_class_new(mcs, name, bases, attrs)

        real_init = getattr(new_class, '__init__')

        def _lazy_init(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs
        setattr(new_class, '__init__', _lazy_init)
        setattr(new_class, '_lazy_init', real_init)

        return new_class


# Wraps return data to JSON
def json_view(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        r = fn(request, *args, **kwargs)
        if isinstance(r, dict) and not isinstance(r.get('text'), str):
            r['text'] = str(r.get('text'))
        return JsonResponse(r, safe=False, json_dumps_params={
            'ensure_ascii': False
        })
    return wrapped
