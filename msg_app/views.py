from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Conversation, MessageError
from .forms import ConversationForm, MessageForm


@login_required
def home(request):
    conversations = Conversation.objects.filter(participants__in=[request.user])
    return render(request, 'msg_app/conversations.html', {
        'conversations': conversations
    })


@login_required
def new_conversation(request):
    try:
        frm = ConversationForm(request.POST or None)
        if request.method == 'POST' and frm.is_valid():
            conv = frm.create(request.user)
            messages.success(request, _('Conversation has been created'))
            return redirect('msg_app:to_conversation', conv.pk)
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
                print(frm)
                messages.error(request, _('fix form errors'))
        msg_list = conv.get_messages()
        return render(request, 'msg_app/chat.html', {
            'conv': conv,
            'msg_list': msg_list
        })
    except MessageError as e:
        messages.error(request, e)
        return redirect('msg_app:home')
