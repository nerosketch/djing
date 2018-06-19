from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView, CreateView

from guardian.decorators import permission_required_or_403 as permission_required
from djing.global_base_views import BaseOrderedFilteringList
from ip_pool import models, forms


@method_decorator(login_required, name='dispatch')
class NetworksListView(BaseOrderedFilteringList):
    device_kind_code = None
    template_name = 'ip_pool/network_list.html'
    context_object_name = 'networks_list'
    model = models.NetworkModel

    def get_queryset(self):
        qs = super().get_queryset()
        if isinstance(self.device_kind_code, str):
            return qs.filter(kind=self.device_kind_code)
        return qs


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('ip_pool.change_networkmodel'), name='dispatch')
class NetworkUpdateView(UpdateView):
    model = models.NetworkModel
    template_name = 'ip_pool/net_edit.html'
    form_class = forms.NetworkForm
    pk_url_kwarg = 'net_id'

    def form_valid(self, form):
        r = super().form_valid(form)
        messages.success(self.request, _('Network successfully updated'))
        return r


@method_decorator(login_required, name='dispatch')
class IpEmployedListView(BaseOrderedFilteringList):
    template_name = 'ip_pool/employed_ip_list.html'
    model = models.EmployedIpModel

    def get_context_data(self, **kwargs):
        net_id = self.kwargs.get('net_id')
        context = super().get_context_data(**kwargs)
        context['net'] = get_object_or_404(models.NetworkModel, pk=net_id)
        return context

    def get_queryset(self):
        net_id = self.kwargs.get('net_id')
        return self.model.objects.filter(network__id=net_id)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('ip_pool.add_networkmodel'), name='dispatch')
class NetworkCreateView(CreateView):
    model = models.NetworkModel
    template_name = 'ip_pool/net_add.html'
    form_class = forms.NetworkForm

    def form_valid(self, form):
        r = super().form_valid(form)
        messages.success(self.request, _('Network has been created'))
        return r
