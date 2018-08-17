from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import MessageFailure
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from guardian.decorators import permission_required_or_403 as permission_required
from guardian.shortcuts import assign_perm
from nas_app.forms import NasForm
from nas_app.models import NASModel


@method_decorator(login_required, name='dispatch')
class NasListView(ListView):
    model = NASModel


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('nas_app.add_nasmodel'), name='dispatch')
class NasCreateView(CreateView):
    model = NASModel
    form_class = NasForm
    template_name = 'nas_app/nasmodel_add.html'
    success_url = reverse_lazy('nas_app:home')

    def form_valid(self, form):
        r = super(NasCreateView, self).form_valid(form)
        assign_perm("nas_app.change_nasmodel", self.request.user, self.object)
        assign_perm("nas_app.can_view_nas", self.request.user, self.object)
        messages.success(self.request, _('New NAS has been created'))
        return r


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('nas_app.delete_nasmodel'), name='dispatch')
class NasDeleteView(DeleteView):
    model = NASModel
    success_url = reverse_lazy('nas_app:home')
    pk_url_kwarg = 'nas_id'

    def delete(self, request, *args, **kwargs):
        try:
            r = super(NasDeleteView, self).delete(request, *args, **kwargs)
            messages.success(request, _('Server successfully removed'))
            return r
        except MessageFailure as e:
            messages.error(request, e)
        failure_url = resolve_url('nas_app:edit', self.object.pk)
        return HttpResponseRedirect(failure_url)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('nas_app.change_nasmodel'), name='dispatch')
class NasUpdateView(UpdateView):
    model = NASModel
    form_class = NasForm
    pk_url_kwarg = 'nas_id'
    template_name = 'nas_app/nasmodel_update.html'

    def form_valid(self, form):
        r = super(NasUpdateView, self).form_valid(form)
        messages.success(self.request, _('Update successfully'))
        return r
