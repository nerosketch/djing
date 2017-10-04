# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from abonapp.models import Abon
from django.utils.translation import ugettext as _
from datetime import date
from guardian.decorators import permission_required_or_403 as permission_required

from .handle import TaskException
from .models import Task
from mydefs import pag_mn, only_admins, safe_int, MultipleException, RuTimedelta
from .forms import TaskFrm


@login_required
@only_admins
def home(request):
    tasks = Task.objects.filter(recipients=request.user, state='S')  # Новые задачи
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def failed_tasks(request):
    tasks = Task.objects.filter(recipients=request.user, state='C')  # Проваленные
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist_failed.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def finished_tasks(request):
    tasks = Task.objects.filter(recipients=request.user, state='F')  # Выполненные
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist_finish.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def own_tasks(request):
    tasks = Task.objects.filter(author=request.user).exclude(state='F')  # Назначенные мной и не законченная
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist_own.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def my_tasks(request):
    tasks = Task.objects.filter(recipients=request.user)  # Задачи где я учавствовал
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist.html', {
        'tasks': tasks
    })


@login_required
@permission_required('taskapp.can_viewall')
def all_tasks(request):
    tasks = Task.objects.all()
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist_all.html', {
        'tasks': tasks
    })


@login_required
@permission_required('taskapp.delete_task')
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # нельзя удалить назначенную мне задачу
    if request.user not in task.recipients.all():
        task.delete()
    else:
        messages.warning(request, _('You cannot delete task that assigned to you'))
    return redirect('taskapp:home')


@login_required
@only_admins
def view(request, task_id):
    tsk = get_object_or_404(Task, id=task_id)
    toc = date(tsk.time_of_create.year, tsk.time_of_create.month, tsk.time_of_create.day)
    time_diff = tsk.out_date - toc
    return render(request, 'taskapp/view.html', {
        'task': tsk,
        'time_diff': RuTimedelta(time_diff)
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
