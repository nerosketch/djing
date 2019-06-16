from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView

from djing.global_base_views import OrderingMixin
from djing.lib.mixins import LoginAdminMixin, LoginAdminPermissionMixin
from new_customers.forms import CustomerModelForm
from new_customers.models import PotentialSubscriber


class CustomersList(LoginAdminMixin, OrderingMixin, ListView):
    model = PotentialSubscriber


class CustomerDetail(LoginAdminPermissionMixin, DetailView):
    model = PotentialSubscriber
    pk_url_kwarg = 'uid'
    permission_required = 'new_customers.view_potentialsubscriber'


class CustomerNew(LoginAdminMixin, PermissionRequiredMixin, CreateView):
    model = PotentialSubscriber
    form_class = CustomerModelForm
    permission_required = 'new_customers.add_potentialsubscriber'
