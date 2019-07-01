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

    def get_context_data(self, **kwargs):
        model_fields = filter(lambda x: hasattr(self.object, x.name), self.object._meta.fields)
        model_fields = filter(lambda x: getattr(self.object, x.name), model_fields)
        model_fields = filter(lambda x: x.name != 'id', model_fields)
        context = {
            'form': CustomerModelForm(instance=self.object),
            'model_fields': map(lambda f: {
                'verbose_name': f.verbose_name,
                'value': getattr(self.object, f.name)
            }, model_fields)
        }
        context.update(kwargs)
        return super().get_context_data(**context)


class CustomerNew(LoginAdminMixin, PermissionRequiredMixin, CreateView):
    model = PotentialSubscriber
    form_class = CustomerModelForm
    permission_required = 'new_customers.add_potentialsubscriber'
