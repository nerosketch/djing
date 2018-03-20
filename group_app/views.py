from django.views.generic import ListView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from . import models
from . import forms


@method_decorator(login_required, name='dispatch')
class GroupListView(ListView):
    http_method_names = ['get']
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)
    template_name = 'group_app/group_list.html'
    model = models.Group
    context_object_name = 'groups'


@method_decorator(login_required, name='dispatch')
class EditGroupView(UpdateView):
    http_method_names = ['get', 'post']
    template_name = 'group_app/edit_group.html'
    form_class = forms.GroupForm
    model = models.Group
    pk_url_kwarg = 'group_id'
    success_url = reverse_lazy('group_app:group_list')

    def form_valid(self, form):
        messages.success(self.request, _('Group changes has been saved'))
        return super(EditGroupView, self).form_valid(form)

    def form_invalid(self, form):
        messages.success(self.request, _('Please fix form errors'))
        return super(EditGroupView, self).form_invalid(form)


@method_decorator(login_required, name='dispatch')
class AddGroupView(CreateView):
    http_method_names = ['get', 'post']
    template_name = 'group_app/add_group.html'
    form_class = forms.GroupForm
    success_url = reverse_lazy('group_app:group_list')

    def form_valid(self, form):
        messages.success(self.request, _('New group are created'))
        return super(AddGroupView, self).form_valid(form)

    def form_invalid(self, form):
        messages.success(self.request, _('Please fix form errors'))
        return super(AddGroupView, self).form_invalid(form)
