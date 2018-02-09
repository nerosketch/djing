from datetime import datetime
from subprocess import run
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.shortcuts import render_to_text
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from guardian.decorators import permission_required_or_403 as permission_required
from django.db.models import Q
from django.conf import settings

from abonapp.models import Abon
from mydefs import only_admins
from .models import AsteriskCDR, SMSModel
from .forms import SMSOutForm


class BaseListView(ListView):
    http_method_names = ['get']
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


@method_decorator([login_required, permission_required('dialing_app.change_asteriskcdr')], name='dispatch')
class LastCallsListView(BaseListView):
    template_name = 'index.html'
    context_object_name = 'logs'
    queryset = AsteriskCDR.objects.exclude(userfield='request')

    def get_context_data(self, **kwargs):
        context = super(LastCallsListView, self).get_context_data(**kwargs)
        context['title'] = _('Last calls')
        return context


@login_required
@only_admins
def to_abon(request, tel):
    abon = Abon.objects.filter(telephone=tel)
    abon_count = abon.count()
    if abon_count > 1:
        messages.warning(request, _('Multiple users with the telephone number'))
    elif abon_count == 0:
        messages.error(request, _('User with the telephone number not found'))
        return redirect('dialapp:home')
    abon = abon[0]
    if abon.group:
        return redirect('abonapp:abon_home', gid=abon.group.pk, uid=abon.pk)
    else:
        return redirect('abonapp:group_list')


@method_decorator([login_required, only_admins], name='dispatch')
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


@method_decorator([login_required, only_admins], name='dispatch')
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


@method_decorator([login_required, permission_required('dialing_app.can_view_sms')], name='dispatch')
class InboxSMSListView(BaseListView):
    template_name = 'inbox_sms.html'
    context_object_name = 'sms_messages'
    model = SMSModel


@login_required
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
    return render_to_text('modal_send_sms.html', {
        'form': frm,
        'path': path
    }, request=request)
