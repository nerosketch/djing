from datetime import datetime
from subprocess import run
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import ProgrammingError
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from guardian.decorators import permission_required_or_403 as permission_required
from django.db.models import Q
from django.conf import settings
from jsonview.decorators import json_view

from abonapp.models import Abon
from djing.global_base_views import SecureApiView
from djing import JSONType
from djing.lib import safe_int
from djing.lib.decorators import only_admins
from .models import AsteriskCDR, SMSModel, SMSOut
from .forms import SMSOutForm


login_decs = login_required, only_admins


class BaseListView(ListView):
    http_method_names = 'get',
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('dialing_app.change_asteriskcdr'), name='dispatch')
class LastCallsListView(BaseListView):
    template_name = 'index.html'
    context_object_name = 'logs'
    queryset = AsteriskCDR.objects.exclude(userfield='request')

    def get(self, request, *args, **kwargs):
        try:
            return super(LastCallsListView, self).get(request, *args, **kwargs)
        except ProgrammingError as e:
            messages.error(self.request, e)
            return redirect('abonapp:group_list')

    def get_context_data(self, **kwargs):
        context = super(LastCallsListView, self).get_context_data(**kwargs)
        context['title'] = _('Last calls')
        return context


@login_required
@only_admins
def to_abon(request, tel):
    abon = Abon.objects.filter(Q(telephone__icontains=tel) | Q(additional_telephones__telephone__icontains=tel))
    abon_count = abon.count()
    if abon_count > 1:
        messages.warning(request, _('Multiple users with the telephone number'))
    elif abon_count == 0:
        messages.error(request, _('User with the telephone number not found'))
        return redirect('dialapp:home')
    abon = abon[0]
    if abon.group:
        return redirect('abonapp:abon_home', gid=abon.group.pk, uname=abon.username)
    else:
        return redirect('abonapp:group_list')


@method_decorator(login_decs, name='dispatch')
class VoiceMailRequestsListView(BaseListView):
    template_name = 'vmail.html'
    context_object_name = 'vmessages'
    queryset = AsteriskCDR.objects.filter(userfield='request')

    def get_context_data(self, **kwargs):
        context = super(VoiceMailRequestsListView, self).get_context_data(**kwargs)
        context['title'] = _('Voice mail request')
        return context


class VoiceMailReportsListView(VoiceMailRequestsListView):
    queryset = AsteriskCDR.objects.filter(userfield='report')

    def get_context_data(self, **kwargs):
        context = super(VoiceMailRequestsListView, self).get_context_data(**kwargs)
        context['title'] = _('Voice mail report')
        return context


@method_decorator(login_decs, name='dispatch')
class DialsFilterListView(BaseListView):
    context_object_name = 'logs'
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(DialsFilterListView, self).get_context_data(**kwargs)
        context['title'] = _('Find dials')
        context['s'] = self.request.GET.get('s')
        context['sd'] = self.request.GET.get('sd')
        return context

    def get_queryset(self):
        s = self.request.GET.get('s')
        sd = self.request.GET.get('sd')
        if isinstance(s, str) and s != '':
            cdr_q = Q(src__icontains=s) | Q(dst__icontains=s)
        else:
            cdr_q = None
        try:
            if isinstance(sd, str) and sd != '':
                sd_date = datetime.strptime(sd, '%Y-%m-%d')
                if cdr_q:
                    cdr_q |= Q(calldate__date=sd_date)
                else:
                    cdr_q = Q(calldate__date=sd_date)
        except ValueError:
            messages.add_message(self.request, messages.ERROR, _('Make sure that your date format is correct'))
        if cdr_q is None:
            cdr = AsteriskCDR.objects.all()
        else:
            cdr = AsteriskCDR.objects.filter(cdr_q)
        return cdr


@method_decorator(login_decs, name='dispatch')
@method_decorator(permission_required('dialing_app.can_view_sms'), name='dispatch')
class InboxSMSListView(BaseListView):
    template_name = 'inbox_sms.html'
    context_object_name = 'sms_messages'
    model = SMSModel


@login_required
@only_admins
@permission_required('dialing_app.can_send_sms')
def send_sms(request):
    path = request.GET.get('path')
    initial_dst = request.GET.get('dst')
    if request.method == 'POST':
        frm = SMSOutForm(request.POST)
        if frm.is_valid():
            frm.save()
            messages.success(request, _('Message was enqueued for sending'))
            pidfile_name = '/run/dialing.py.pid'
            try:
                with open(pidfile_name, 'r') as f:
                    pid = int(f.read())
                run(['/usr/bin/kill', '-SIGUSR1', str(pid)])
            except FileNotFoundError:
                print('Failed sending, %s not found' % pidfile_name)
            if path:
                return redirect(path)
            else:
                return redirect('dialapp:inbox_sms')
        else:
            messages.error(request, _('fix form errors'))
    else:
        frm = SMSOutForm(initial={'dst': initial_dst})
    return render(request, 'modal_send_sms.html', {
        'form': frm,
        'path': path
    })


class SmsManager(SecureApiView):
    #
    # Api view for management sms from dongle
    #
    http_method_names = ('get',)

    @staticmethod
    def bad_cmd() -> JSONType:
        return {'text': 'Command is not allowed'}

    @method_decorator(json_view)
    def get(self, request, *args, **kwargs):
        cmd = request.GET.get('cmd')
        data = request.GET.dict()
        handler = getattr(self, cmd.lower(), self.bad_cmd)
        del data['cmd']
        del data['sign']
        return handler(**data)

    @staticmethod
    def save_sms(**kwargs) -> JSONType:
        sms = SMSModel.objects.create(
            who=kwargs.get('who'),
            dev=kwargs.get('dev'),
            text=kwargs.get('text')
        )
        return {'status': 'ok', 'sms_id': sms.pk}

    @staticmethod
    def update_status(**kwargs) -> JSONType:
        msg_id = safe_int(kwargs.get('mid'))
        if msg_id != 0:
            status = kwargs.get('status')
            update_count = SMSOut.objects.filter(pk=msg_id).update(status=status)
            return {
                'text': 'Status updated',
                'update_count': update_count
            }
        return {'text': 'Bad mid parameter'}

    @staticmethod
    def get_new() -> JSONType:
        msgs = SMSOut.objects.filter(status='nw').defer('status')
        res = [{
            'when': round(m.timestamp),
            'dst': m.dst,
            'text': m.text
        } for m in msgs]
        return res
