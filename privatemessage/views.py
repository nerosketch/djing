# -*- coding: utf-8 -*-
from json import dumps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template.context_processors import csrf
from django.contrib.auth import get_user_model

from .models import PrivateMessages
import mydefs


@login_required
@mydefs.only_admins
def home(request):
    msgs = PrivateMessages.objects.all()
    return render(request, 'private_messages/index.html', {
        'msgs': msgs
    })


@login_required
@mydefs.only_admins
def delitem(request, id=0):
    r = {'errnum': 0, 'errtext': ''}
    try:
        PrivateMessages.objects.get(id=id).delete()
    except PrivateMessages.DoesNotExist:
        r = {
            'errnum': 1,
            'errtext': 'Error while deleting, item does not exist'
        }
    return HttpResponse(dumps(r))


@login_required
@mydefs.only_admins
def send_message(request):
    UserModel = get_user_model()
    if request.method == 'GET':
        return HttpResponse(render_to_string('private_messages/send_form.html', {
            'csrf_token': csrf(request)['csrf_token'],
            'a': request.GET.get('a')
        }))
    elif request.method == 'POST':
        try:
            a = request.GET.get('a')
            a = 0 if a is None or a == '' else int(a)
            msg = PrivateMessages()
            msg.sender = request.user
            msg.recepient = UserModel.objects.get(id=a)
            msg.text = request.POST.get('msg_text')
            msg.save()
            return redirect('privmsg:home')
        except UserModel.DoesNotExist:
            return mydefs.res_error(request, 'Адресат не найден')
    else:
        return mydefs.res_error(request, 'Ошибка типа запроса')
