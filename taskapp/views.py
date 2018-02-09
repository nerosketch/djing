# coding=utf-8
from json import dumps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.utils.translation import ugettext as _
from django.conf import settings

from datetime import datetime
from guardian.decorators import permission_required_or_403 as permission_required
from chatbot.models import MessageQueue
from abonapp.models import Abon
from .handle import TaskException
from .models import Task
from mydefs import only_admins, safe_int, MultipleException, RuTimedelta
from .forms import TaskFrm


class BaseTaskListView(ListView):
    http_method_names = ['get']
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


@method_decorator([login_required, only_admins], name='dispatch')
class NewTasksView(BaseTaskListView):
    """
    Show new tasks
    """
    template_name = 'taskapp/tasklist.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='S') \
                           .select_related('abon', 'abon__street', 'abon__group', 'author')


class FailedTasksView(NewTasksView):
    """
    Show crashed tasks
    """
    template_name = 'taskapp/tasklist_failed.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='C') \
                           .select_related('abon', 'abon__street', 'abon__group', 'author')


class FinishedTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist_finish.html'

    def get_queryset(self):
        return Task.objects.filter(recipients=self.request.user, state='F') \
                           .select_related('abon', 'abon__street', 'abon__group', 'author')


class OwnTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist_own.html'

    def get_queryset(self):
        # Attached and not finished tasks
        return Task.objects.filter(author=self.request.user)\
                           .exclude(state='F')\
                           .select_related('abon', 'abon__street', 'abon__group')


class MyTaskListView(NewTasksView):
    template_name = 'taskapp/tasklist.html'

    def get_queryset(self):
        # Tasks in which I participated
        return Task.objects.filter(recipients=self.request.user) \
                           .select_related('abon', 'abon__street', 'abon__group', 'author')


@method_decorator([login_required, permission_required('taskapp.can_viewall')], name='dispatch')
class AllTasksListView(BaseTaskListView):
    template_name = 'taskapp/tasklist_all.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.select_related('abon', 'abon__street', 'abon__group', 'author')


@login_required
@permission_required('taskapp.delete_task')
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # нельзя удалить назначенную мне задачу
    if request.user.is_superuser or request.user not in task.recipients.all():
        task.delete()
    else:
        messages.warning(request, _('You cannot delete task that assigned to you'))
    return redirect('taskapp:home')


@login_required
@only_admins
def view(request, task_id):
    tsk = get_object_or_404(Task, id=task_id)
    #toc = date(tsk.time_of_create.year, tsk.time_of_create.month, tsk.time_of_create.day)
    now_date = datetime.now().date()
    if tsk.out_date > now_date:
        time_diff = "%s: %s" % (_('time left'), RuTimedelta(tsk.out_date - now_date))
    else:
        time_diff = _("Expired timeout -%(time_left)s") % {'time_left': RuTimedelta(now_date - tsk.out_date)}
    return render(request, 'taskapp/view.html', {
        'task': tsk,
        'time_diff': time_diff
    })


@login_required
@only_admins
def task_add_edit(request, task_id=0):
    task_id = safe_int(task_id)
    uid = request.GET.get('uid', 0)
    selected_abon = None
    frm = TaskFrm()

    # чтоб при добавлении сразу был выбран исполнитель
    #frm_recipient_id = safe_int(request.GET.get('rp'))

    if task_id == 0:
        if not request.user.has_perm('taskapp.add_task'):
            raise PermissionDenied
        tsk = Task()
    else:
        if not request.user.has_perm('taskapp.change_task'):
            raise PermissionDenied
        tsk = get_object_or_404(Task, id=task_id)
        frm = TaskFrm(instance=tsk)
        selected_abon = tsk.abon

    try:
        if request.method == 'POST':
            tsk.author = request.user
            frm = TaskFrm(request.POST, request.FILES, instance=tsk)

            if frm.is_valid():
                task_instance = frm.save()
                # получим абонента, выбранного в форме
                selected_abon = task_instance.abon
                if selected_abon:
                    # получаем аккаунты назначенные на группу выбранного абонента
                    profiles = selected_abon.group.profiles.filter(is_active=True).filter(is_admin=True)

                    # если нашли кого-нибудь
                    if profiles.count() > 0:
                        # выбираем их id в базе
                        profile_ids = [prof.id for prof in profiles]
                        # добавляем найденных работников в задачу
                        task_instance.recipients.add(*profile_ids)
                        # окончательно сохраняемся
                        task_instance.save()
                        return redirect('taskapp:home')
                    else:
                        messages.error(request, _('No responsible employee for the users group'))
                else:
                    messages.error(request, _('You must select the subscriber'))
            else:
                messages.error(request, _('Error in the form fields'))
        elif uid:
            selected_abon = Abon.objects.get(username=str(uid))
    except Abon.DoesNotExist:
        messages.warning(request, _("User does not exist"))
    except MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except TaskException as e:
        messages.error(request, e)

    return render(request, 'taskapp/add_edit_task.html', {
        'form': frm,
        'task_id': tsk.id,
        'selected_abon': selected_abon
    })


@login_required
@only_admins
def task_finish(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task.finish(request.user)
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
    except TaskException as e:
        messages.error(request, e)
    return redirect('taskapp:home')


@login_required
@permission_required('taskapp.can_remind')
def remind(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task.save(update_fields=['state'])
    except MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except TaskException as e:
        messages.error(request, e)
    return redirect('taskapp:home')


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
    return HttpResponse(dumps(r))
