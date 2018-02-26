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
        if API_AUTH_SECRET is None or API_AUTH_SECRET == 'your api secret':
            raise NotImplementedError('You must specified API_AUTH_SECRET in settings')
        else:
            super(HashAuthView, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        sign = request.GET.get('sign')
        if sign is None or sign == '':
            return HttpResponseForbidden('Access Denied')

        # Transmittent get list without sign
        get_values = request.GET.copy()
        del get_values['sign']
        heshable = (get_values.get('ip'), get_values.get('status'), API_AUTH_SECRET)
        if HashAuthView.check_sign(heshable, sign):
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


class OrderingMixin(object):
    """
    Ordering result object list by @order_by variable in get request.
    For example url?order_by=username orders objects by username.
    @dir - direction of ordering. down or up.
    @order_by - ordering field name
    """
    def get_context_data(self, **kwargs):
        context = super(OrderingMixin, self).get_context_data(**kwargs)
        context['order_by'] = self.request.GET.get('order_by')
        direction = self.request.GET.get('dir')
        if direction == 'down':
            direction = 'up'
        elif direction == 'up':
            direction = 'down'
        else:
            direction = ''
        context['dir'] = direction
        return context

    def get_ordering(self):
        direction = self.request.GET.get('dir')
        order_by = self.request.GET.get('order_by')
        dfx = ''
        if direction == 'down':
            dfx = '-'
        if order_by:
            return "%s%s" % (dfx, order_by)
