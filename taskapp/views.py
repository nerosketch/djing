# coding=utf-8
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from abonapp.models import Abon

from models import Task
from mydefs import pag_mn, only_admins, safe_int
from forms import TaskFrm


@login_required
@only_admins
def home(request):
    tasks = Task.objects.filter(recipient=request.user, state='S')  # Новые задачи

    # filter
    # dir, field = order_helper(request)
    #if field:
    #    tasks = tasks.order_by(field)

    tasks = pag_mn(request, tasks)

    return render(request, 'taskapp/tasklist.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def active_tasks(request):
    tasks = Task.objects.filter(recipient=request.user, state='C')  # На выполнении
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist_active.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def finished_tasks(request):
    tasks = Task.objects.filter(recipient=request.user, state='F')  # Выполненные
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
    tasks = Task.objects.filter(recipient=request.user)  # Все задачи
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist.html', {
        'tasks': tasks
    })


@login_required
@permission_required('taskapp.can_viewall')
def all_tasks(request):
    tasks = Task.objects.all()
    return render(request, 'taskapp/tasklist_all.html', {
        'tasks': tasks
    })


@login_required
@permission_required('taskapp.can_delete_task')
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user != task.recipient:
        task.delete()
    return redirect('taskapp:home')


@login_required
@permission_required('taskapp.can_change_task')
def task_add_edit(request, task_id=0):
    task_id = safe_int(task_id)
    warntext = ''

    uid = request.GET.get('uid')
    selected_abon = None

    # чтоб при добавлении сразу был выбран исполнитель
    frm_recipient_id = safe_int(request.GET.get('rp'))
    if task_id == 0:
        tsk = Task()
        tsk.author = request.user
    else:
        tsk = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        frm = TaskFrm(request.POST, request.FILES, instance=tsk)
        if frm.is_valid():
            frm.save()
            return redirect('taskapp:home')
        else:
            warntext = u'Исправте ошибки'
    else:
        if task_id == 0:
            try:
                uid = int(uid or 0)
                selected_abon = None if uid == 0 else get_object_or_404(Abon, username=str(uid))
                frm = TaskFrm(initial={
                    'recipient': frm_recipient_id,
                    'abon': selected_abon
                })
            except ValueError:
                warntext=u'Передаваемый логин абонента должен состоять только из цифр'
                frm = TaskFrm(initial={
                    'recipient': frm_recipient_id
                })
        else:
            frm = TaskFrm(instance=tsk)
            selected_abon = tsk.abon

    return render(request, 'taskapp/add_edit_task.html', {
        'warntext': warntext,
        'form': frm,
        'task_id': tsk.id,
        'selected_abon': selected_abon
    })


@login_required
@only_admins
def task_finish(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.finish(request.user)
    task.save(update_fields=['state', 'out_date'])
    return redirect('taskapp:home')


@login_required
@only_admins
def task_begin(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.begin(request.user)
    task.save(update_fields=['state'])
    return redirect('taskapp:home')
