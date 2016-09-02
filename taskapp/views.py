# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from models import Task
from mydefs import pag_mn#, order_helper
from forms import TaskFrm


@login_required
def home(request):
    tasks = Task.objects.all()

    # filter
    #dir, field = order_helper(request)
    #if field:
    #    tasks = tasks.order_by(field)

    for ts in tasks:
        print ts.priority, type(ts.priority)

    tasks = pag_mn(request, tasks)

    return render(request, 'taskapp/index.html', {
        'tasks': tasks
    })


@login_required
def task_delete(request, task_id):
    get_object_or_404(Task, id=task_id).delete()
    return redirect('task_home')


@login_required
def task_add_edit(request, task_id=0):
    warntext = ''
    if request.method == 'POST':
        frm = TaskFrm(request.POST)
        if frm.is_valid():
            tsk = Task()
            tsk.save_form(frm, request.user)
            tsk.save()
            return redirect('task_home')
        else:
            warntext = u'Исправте ошибки'

    if task_id == 0:
        task = Task()
        frm = TaskFrm()
    else:
        task = get_object_or_404(Task, id=task_id)
        frm = TaskFrm({
            'descr': task.descr,
            'recipient': task.recipient.id,
            'device': task.device.id,
            'priority': task.priority,
            'out_date': task.out_date
        })

    return render(request, 'taskapp/add_edit_task.html', {
        'warntext': warntext,
        'form': frm,
        'task': task
    })
