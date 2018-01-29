from hashlib import sha256
from django.views.generic.base import View
from django.http.response import HttpResponseForbidden
from django.conf import settings
from netaddr import IPNetwork, IPAddress


API_AUTH_SECRET = getattr(settings, 'API_AUTH_SECRET')
API_AUTH_SUBNET = getattr(settings, 'API_AUTH_SUBNET')


class HashAuthView(View):

    @staticmethod
    def calc_hash(data):
        if type(data) is str:
            result_data = data.encode('utf-8')
        else:
            result_data = bytes(data)
        return sha256(result_data).hexdigest()

    @staticmethod
    def check_sign(get_list, sign):
        hashed = '_'.join(get_list)
        my_sign = HashAuthView.calc_hash(hashed)
        return sign == my_sign

    def __init__(self, *args, **kwargs):
        if API_AUTH_SECRET is None:
            raise ImportError('You must specified API_AUTH_SECRET is settings')
        else:
            super(HashAuthView, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        sign = request.GET.get('sign')

        # Transmittent get list without sign
        get_values = request.GET.copy()
        del get_values['sign']
        if HashAuthView.check_sign(list(get_values.values()) + [API_AUTH_SECRET], sign):
            return super(HashAuthView, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Access Denied')


class AllowedSubnetMixin(object):

    def dispatch(self, request, *args, **kwargs):
        """
        Check if user ip in allowed subnet.
        Return 403 denied otherwise.
        """
        ip = IPAddress(request.META.get('REMOTE_ADDR'))
        if ip in IPNetwork(API_AUTH_SUBNET):
            return super(AllowedSubnetMixin, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Access Denied')
