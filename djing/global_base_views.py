from hashlib import sha256
from json import dumps
from django.views.generic.base import View
from django.http.response import HttpResponseForbidden, Http404, HttpResponseRedirect, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.generic import ListView
from netaddr import IPNetwork, IPAddress
from django.core.paginator import InvalidPage, EmptyPage

API_AUTH_SECRET = getattr(settings, 'API_AUTH_SECRET')
API_AUTH_SUBNET = getattr(settings, 'API_AUTH_SUBNET')


class RedirectWhenError(Exception):
    def __init__(self, url, failed_message=None):
        self.url = url
        if failed_message is not None:
            self.message = failed_message

    def __str__(self):
        return self.message or ''


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
        values_list = [l for l in get_values.values() if l]
        values_list.sort()
        values_list.append(API_AUTH_SECRET)
        if self.check_sign(values_list, sign):
            return super(HashAuthView, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Access Denied')


class AuthenticatedOrHashAuthView(HashAuthView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if request.user.is_admin:
                return View.dispatch(self, request, *args, **kwargs)
            else:
                return HttpResponseRedirect('client_side:home')
        else:
            return HashAuthView.dispatch(self, request, *args, **kwargs)


class AllowedSubnetMixin(object):
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user ip in allowed subnet.
        Return 403 denied otherwise.
        """
        ip = IPAddress(request.META.get('REMOTE_ADDR'))
        if type(API_AUTH_SUBNET) is str:
            if ip in IPNetwork(API_AUTH_SUBNET):
                return super(AllowedSubnetMixin, self).dispatch(request, *args, **kwargs)
        try:
            for subnet in API_AUTH_SUBNET:
                if ip in IPNetwork(subnet):
                    return super(AllowedSubnetMixin, self).dispatch(request, *args, **kwargs)
        except TypeError:
            if ip in IPNetwork(str(API_AUTH_SUBNET)):
                return super(AllowedSubnetMixin, self).dispatch(request, *args, **kwargs)
        return HttpResponseForbidden('Access Denied')


class SecureApiView(AllowedSubnetMixin, HashAuthView):
    pass


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


class RedirectWhenErrorMixin(object):
    def get(self, request, *args, **kwargs):
        try:
            return super(RedirectWhenErrorMixin, self).get(request, *args, **kwargs)
        except RedirectWhenError as e:
            if request.is_ajax():
                return HttpResponse(dumps({
                    'url': e.url,
                    'text': e.message or ''
                }))
            else:
                return HttpResponseRedirect(e.url)


class BaseListWithFiltering(RedirectWhenErrorMixin, ListView):
    """
    When queryset contains filter and pagination than data may be missing,
    and original code is raising 404 error. We want to redirect without pagination.
    """

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset, page_size, orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty())
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except EmptyPage:
            # remove pagination from url
            url = self.request.GET.copy()
            del url[self.page_kwarg]
            raise RedirectWhenError("%s?%s" % (self.request.path, url.urlencode()),
                                    _('Filter does not contains data, filter without pagination'))
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                'page_number': page_number,
                'message': str(e)
            })
