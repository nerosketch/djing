from json import dumps
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from chatbot.models import MessageQueue

from mydefs import pag_mn
from .models import Conversation, MessageError, Message
from .forms import ConversationForm, MessageForm


@login_required
def home(request):
    # TODO: optimise queries
    conversations = Conversation.objects.fetch(request.user)
    conversations = pag_mn(request, conversations, 8)
    return render(request, 'msg_app/conversations.html', {
        'conversations': conversations
    })


@login_required
def new_conversation(request):
    try:
        frm = ConversationForm(request.POST or None)
        if request.method == 'POST':
            if frm.is_valid():
                conv = frm.create(request.user)
                messages.success(request, _('Conversation has been created'))
                return redirect('msg_app:to_conversation', conv.pk)
            else:
                messages.error(request, _('fix form errors'))
        else:
            return render_to_text('msg_app/modal_new_conversation.html', {
                'form': frm
            }, request=request)
    except MessageError as e:
        messages.error(request, e)
        return redirect('msg_app:home')


@login_required
def to_conversation(request, conv_id):
    conv = get_object_or_404(Conversation, pk=conv_id)
    try:
        if request.method == 'POST':
            frm = MessageForm(request.POST, request.FILES)
            if frm.is_valid():
                frm.create(conv, request.user)
            else:
                messages.error(request, _('fix form errors'))
        else:
            conv.make_messages_status_old(request.user)
        msg_list = conv.get_messages()
        return render(request, 'msg_app/chat.html', {
            'conv': conv,
            'msg_list': msg_list
        })
    except MessageError as e:
        messages.error(request, e)
        return redirect('msg_app:home')


@login_required
def remove_msg(request, conv_id, msg_id):
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.author != request.user:
        raise PermissionDenied
    conversation_id = msg.conversation.pk
    msg.delete()
    return redirect('msg_app:to_conversation', conversation_id)


@login_required
def check_news(request):
    msg = MessageQueue.objects.pop(user=request.user, tag='msgapp')
    if msg is not None:
        r = {
            'exist': True,
            'content': msg,
            'title': "%s" % _('Message')
        }
    else:
        r = {'exist': False}
    return HttpResponse(dumps(r))
