from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView

from djing.lib.decorators import only_admins
from guardian.decorators import permission_required_or_403 as permission_required

from .models import Conversation, MessageError, Message
from .forms import ConversationForm, MessageForm


login_decs = login_required, only_admins


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('msg_app.view_conversation'), name='dispatch')
class ConversationsListView(ListView):
    context_object_name = 'conversations'
    template_name = 'msg_app/conversations.html'

    def get_queryset(self):
        # TODO: optimise queries
        return Conversation.objects.fetch(self.request.user)


@login_required
@only_admins
@permission_required('msg_app.add_conversation')
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
            return render(request, 'msg_app/modal_new_conversation.html', {
                'form': frm
            })
    except MessageError as e:
        messages.error(request, e)
        return redirect('msg_app:home')


@login_required
@only_admins
@permission_required('msg_app.view_conversation')
def to_conversation(request, conv_id):
    conv = get_object_or_404(Conversation, pk=conv_id)
    try:
        if request.method == 'POST':
            frm = MessageForm(request.POST, request.FILES)
            if frm.is_valid():
                frm.create(conv, request.user)
                return redirect(conv.get_absolute_url())
            else:
                messages.error(request, _('fix form errors'))
        else:
            conv.make_messages_status_old(request.user)
            frm = MessageForm()
        msg_list = conv.get_messages()
        return render(request, 'msg_app/chat.html', {
            'conv': conv,
            'msg_list': msg_list,
            'msg_form': frm
        })
    except MessageError as e:
        messages.error(request, e)
        return redirect('msg_app:home')


@login_required
@only_admins
@permission_required('msg_app.delete_message')
def remove_msg(request, conv_id, msg_id):
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.author != request.user:
        raise PermissionDenied
    conversation_id = msg.conversation.pk
    msg.delete()
    return redirect('msg_app:to_conversation', conversation_id)
