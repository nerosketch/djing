from functools import wraps
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


DEBUG = getattr(settings, 'DEBUG', False)


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
