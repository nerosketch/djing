# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from models import PrivateMessages
from django.http import HttpResponse
from json import dumps
from django.template.context_processors import csrf
import mydefs
from accounts_app.models import UserProfile


@login_required
def home(request):
    msgs = PrivateMessages.objects.all()
    return render(request, 'private_messages/index.html', {
        'msgs': msgs
    })


@login_required
def delitem(request, id=0):
    r = {'errnum': 0,'errtext': u''}
    try:
        PrivateMessages.objects.get(id=id).delete()
    except PrivateMessages.DoesNotExist:
        r = {
            'errnum': 1,
            'errtext': u'Error while deleting, item does not exist'
        }
    return HttpResponse(dumps(r))


@login_required
def send_message(request):
    if request.method == 'GET':
        return HttpResponse(render_to_string('private_messages/send_form.html',{
            'csrf_token': csrf(request)['csrf_token'],
            'a': request.GET.get('a')
        }))
    elif request.method == 'POST':
        try:
            a = request.GET.get('a')
            a = 0 if a is None or a == '' else int(a)
            msg = PrivateMessages()
            msg.sender = request.user
            msg.recepient = UserProfile.objects.get(id=a)
            msg.text = request.POST.get('msg_text')
            msg.save()
            return redirect('privmsg_home')
        except UserProfile.DoesNotExist:
            return mydefs.res_error(request, u'Адресат не найден')
    else:
        return mydefs.res_error(request, u'Ошибка типа запроса')
