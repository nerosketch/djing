# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from models import Task
from mydefs import pag_mn, only_admins, safe_int
from forms import TaskFrm


@login_required
@only_admins
def home(request):
    tasks = Task.objects.filter(recipient=request.user, state='S')  # Новые задачи

    # filter
    #dir, field = order_helper(request)
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
def all_tasks(request):
    tasks = Task.objects.filter(recipient=request.user)  # Все задачи
    tasks = pag_mn(request, tasks)
    return render(request, 'taskapp/tasklist.html', {
        'tasks': tasks
    })


@login_required
@only_admins
def task_delete(request, task_id):
    get_object_or_404(Task, id=task_id).delete()
    return redirect('task_home')


@login_required
@only_admins
def task_add_edit(request, task_id=0):
    task_id = int(task_id)
    warntext = ''

    # чтоб при добавлении сразу был выбран исполнитель
    frm_recipient_id = safe_int(request.GET.get('rp'))

    if request.method == 'POST':
        frm = TaskFrm(request.POST)
        if frm.is_valid():
            if task_id == 0:
                tsk = Task()
            else:
                tsk = get_object_or_404(Task, id=task_id)
            tsk.save_form(frm, request.user)
            tsk.save()
            return redirect('task_home')
        else:
            warntext = u'Исправте ошибки'

    if task_id == 0:
        task = Task()
        frm = TaskFrm(initial={
            'recipient': frm_recipient_id
        })
    else:
        task = get_object_or_404(Task, id=task_id)
        frm = TaskFrm({
            'descr': task.descr,
            'recipient': task.recipient.id,
            'device': task.device.id,
            'priority': task.priority,
            'out_date': task.out_date,
            'state': task.state
        })

    return render(request, 'taskapp/add_edit_task.html', {
        'warntext': warntext,
        'form': frm,
        'task': task
    })


@login_required
@only_admins
def task_finish(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.finish(request.user)
    task.save()
    return redirect('task_home')


@login_required
@only_admins
def task_begin(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.begin(request.user)
    task.save()
    return redirect('task_home')
