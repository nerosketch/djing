from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import redirect, get_object_or_404, resolve_url
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from django.utils.translation import ugettext as _
from django.conf import settings

from datetime import datetime

from django.views.generic.edit import FormMixin, DeleteView, UpdateView
from guardian.decorators import permission_required_or_403 as permission_required
from jsonview.decorators import json_view

from chatbot.models import MessageQueue
from abonapp.models import Abon
from djing import httpresponse_to_referrer
from djing.lib import safe_int, MultipleException, RuTimedelta
from djing.lib.decorators import only_admins
from .handle import TaskException
from .models import Task, ExtraComment
from .forms import TaskFrm, ExtraCommentForm


login_decs = login_required, only_admins


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class NewTasksView(ListView):
    """
    Show new tasks
    """
    http_method_names = ('get',)
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)
    template_name = 'taskapp/tasklist.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='S') \
            .annotate(comment_count=Count('extracomment')) \
            .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class FailedTasksView(NewTasksView):
    """
    Show crashed tasks
    """
    template_name = 'taskapp/tasklist_failed.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='C') \
            .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class FinishedTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist_finish.html'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='F') \
            .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class OwnTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist_own.html'

    def get_queryset(self):
        # Attached and not finished tasks
        return Task.objects.filter(author=self.request.user) \
            .exclude(state='F') \
            .select_related('abon', 'abon__street', 'abon__group')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class MyTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist.html'

    def get_queryset(self):
        # Tasks in which I participated
        return Task.objects.filter(recipients=self.request.user) \
            .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.can_viewall'), name='dispatch')
class AllTasksListView(ListView):
    http_method_names = ('get',)
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)
    template_name = 'taskapp/tasklist_all.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.annotate(comment_count=Count('extracomment')) \
            .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.view_task'), name='dispatch')
class EmptyTasksListView(NewTasksView):
    template_name = 'taskapp/tasklist_empty.html'

    def get_queryset(self):
        return Task.objects.annotate(reccount=Count('recipients')).filter(reccount__lt=1)


@login_required
@only_admins
@permission_required('taskapp.delete_task')
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # prevent to delete task that assigned to me
    if request.user.is_superuser or request.user not in task.recipients.all():
        task.delete()
    else:
        messages.warning(request, _('You cannot delete task that assigned to you'))
    return redirect('taskapp:home')


@method_decorator(login_decs, name='dispatch')
class TaskUpdateView(UpdateView):
    http_method_names = ('get', 'post')
    template_name = 'taskapp/add_edit_task.html'
    form_class = TaskFrm
    context_object_name = 'task'

    def get_object(self, queryset=None):
        task_id = safe_int(self.kwargs.get('task_id'))
        if task_id == 0:
            uname = self.request.GET.get('uname')
            if uname:
                self.selected_abon = Abon.objects.get(username=uname)
            return
        else:
            task = get_object_or_404(Task, pk=task_id)
            self.selected_abon = task.abon
            return task

    def dispatch(self, request, *args, **kwargs):
        task_id = safe_int(self.kwargs.get('task_id', 0))
        if task_id == 0:
            if not request.user.has_perm('taskapp.add_task'):
                raise PermissionDenied
        else:
            if not request.user.has_perm('taskapp.change_task'):
                raise PermissionDenied
        try:
            return super(TaskUpdateView, self).dispatch(request, *args, **kwargs)
        except TaskException as e:
            messages.error(request, e)
        return httpresponse_to_referrer(request)

    def get_form_kwargs(self):
        kwargs = super(TaskUpdateView, self).get_form_kwargs()
        if hasattr(self, 'selected_abon'):
            kwargs.update({'initial_abon': self.selected_abon})
        return kwargs

    def form_valid(self, form):
        try:
            self.object = form.save()
            if self.object.author is None:
                self.object.author = self.request.user
                self.object.save(update_fields=('author',))
            task_id = safe_int(self.kwargs.get('task_id', 0))
            if task_id == 0:
                log_text = _('Task has successfully created')
            else:
                log_text = _('Task has changed successfully')
            messages.add_message(self.request, messages.SUCCESS, log_text)
            self.object.send_notification()
        except MultipleException as e:
            for err in e.err_list:
                messages.add_message(self.request, messages.WARNING, err)
        except TaskException as e:
            messages.add_message(self.request, messages.ERROR, e)
        return FormMixin.form_valid(self, form)

    def get_context_data(self, **kwargs):
        if hasattr(self, 'selected_abon'):
            selected_abon = self.selected_abon
        else:
            selected_abon = None

        now_date = datetime.now().date()
        task = self.object
        if task:
            if task.out_date > now_date:
                time_diff = "%s: %s" % (_('time left'), RuTimedelta(task.out_date - now_date))
            else:
                time_diff = _("Expired timeout -%(time_left)s") % {'time_left': RuTimedelta(now_date - task.out_date)}
        else:
            time_diff = None

        context = {
            'selected_abon': selected_abon,
            'time_diff': time_diff,
            'comments': ExtraComment.objects.filter(task=task),
            'comment_form': ExtraCommentForm()
        }
        context.update(kwargs)
        return super(TaskUpdateView, self).get_context_data(**context)

    def get_success_url(self):
        task_id = safe_int(self.kwargs.get('task_id'))
        if task_id == 0:
            return resolve_url('taskapp:own_tasks')
        else:
            return resolve_url('taskapp:edit', task_id)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('fix form errors'))
        return super(TaskUpdateView, self).form_invalid(form)


@login_required
@only_admins
def task_finish(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task.finish(request.user)
        task.send_notification()
    except MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except TaskException as e:
        messages.error(request, e)
    return redirect('taskapp:home')


@login_required
@only_admins
def task_failed(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task.do_fail(request.user)
        task.send_notification()
    except TaskException as e:
        messages.error(request, e)
    return redirect('taskapp:home')


@login_required
@only_admins
@permission_required('taskapp.can_remind')
def remind(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task.save(update_fields=('state',))
        task.send_notification()
    except MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except TaskException as e:
        messages.error(request, e)
    return redirect('taskapp:home')


@json_view
def check_news(request):
    if request.user.is_authenticated and request.user.is_admin:
        msg = MessageQueue.objects.pop(user=request.user, tag='taskap')
        if msg is not None:
            r = {
                'auth': True,
                'exist': True,
                'content': msg,
                'title': _('Task')
            }
        else:
            r = {'auth': True, 'exist': False}
    else:
        r = {'auth': False}
    return r


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.add_extracomment'), name='dispatch')
class NewCommentView(CreateView):
    form_class = ExtraCommentForm
    model = ExtraComment
    http_method_names = ('get', 'post')

    def form_valid(self, form):
        self.task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        self.object = form.make_save(
            author=self.request.user,
            task=self.task
        )
        return FormMixin.form_valid(self, form)


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('taskapp.delete_extracomment'), name='dispatch')
class DeleteCommentView(DeleteView):
    model = ExtraComment
    pk_url_kwarg = 'comment_id'
    http_method_names = ('get', 'post')
    template_name = 'taskapp/comments/extracomment_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = {
            'task_id': self.kwargs.get('task_id')
        }
        context.update(kwargs)
        return super(DeleteCommentView, self).get_context_data(**context)

    def get_success_url(self):
        task_id = self.kwargs.get('task_id')
        return resolve_url('taskapp:edit', task_id)
