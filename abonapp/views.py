from typing import Dict, Optional
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, ProgrammingError, transaction
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView, CreateView
from django.conf import settings
from jsonview.decorators import json_view

from agent.commands.dhcp import dhcp_commit, dhcp_expiry, dhcp_release
from statistics.models import StatCache
from tariff_app.models import Tariff
from agent import NasFailedResult, Transmitter, NasNetworkError
from . import forms
from . import models
import mydefs
from devapp.models import Device, Port as DevPort
from datetime import datetime, date, timedelta
from taskapp.models import Task
from dialing_app.models import AsteriskCDR
from statistics.models import getModel
from group_app.models import Group
from guardian.shortcuts import get_objects_for_user, assign_perm
from guardian.decorators import permission_required_or_403 as permission_required
from djing import ping
from djing.global_base_views import OrderingMixin, BaseListWithFiltering, SecureApiView

PAGINATION_ITEMS_PER_PAGE = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


class BaseAbonListView(OrderingMixin, BaseListWithFiltering):
    paginate_by = PAGINATION_ITEMS_PER_PAGE
    http_method_names = ['get']


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
class PeoplesListView(BaseAbonListView):
    context_object_name = 'peoples'
    template_name = 'abonapp/peoples.html'

    def get_queryset(self):
        street_id = mydefs.safe_int(self.request.GET.get('street'))
        gid = mydefs.safe_int(self.kwargs.get('gid'))
        peoples_list = models.Abon.objects.all().select_related('group', 'street', 'current_tariff')
        if street_id > 0:
            peoples_list = peoples_list.filter(group__pk=gid, street=street_id)
        else:
            peoples_list = peoples_list.filter(group__pk=gid)

        try:
            for abon in peoples_list:
                if abon.ip_address is not None:
                    try:
                        abon.stat_cache = StatCache.objects.get(ip=abon.ip_address)
                    except StatCache.DoesNotExist:
                        pass
        except mydefs.LogicError as e:
            messages.warning(self.request, e)
        ordering = self.get_ordering()
        if ordering and isinstance(ordering, str):
            ordering = (ordering,)
            peoples_list = peoples_list.order_by(*ordering)
        return peoples_list

    def get_context_data(self, **kwargs):
        gid = mydefs.safe_int(self.kwargs.get('gid'))
        if gid == 0:
            return HttpResponseBadRequest('group id is broken')
        group = get_object_or_404(Group, pk=gid)
        if not self.request.user.has_perm('group_app.can_view_group', group):
            raise PermissionDenied

        context = super(PeoplesListView, self).get_context_data(**kwargs)

        context['streets'] = models.AbonStreet.objects.filter(group=gid)
        context['street_id'] = mydefs.safe_int(self.request.GET.get('street'))
        context['group'] = group
        return context


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
class GroupListView(BaseAbonListView):
    context_object_name = 'groups'
    template_name = 'abonapp/group_list.html'
    queryset = Group.objects.annotate(usercount=Count('abon'))

    def get_queryset(self):
        queryset = super(GroupListView, self).get_queryset()
        queryset = get_objects_for_user(self.request.user, 'group_app.can_view_group', klass=queryset,
                                        accept_global_perms=False)
        return queryset


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
@method_decorator(permission_required('abonapp.add_abon'), name='dispatch')
class AbonCreateView(CreateView):
    group = None
    abon = None
    form_class = forms.AbonForm
    template_name = 'abonapp/addAbon.html'
    context_object_name = 'group'

    def get_success_url(self):
        return resolve_url('abonapp:abon_home', self.group.id, self.abon.username)

    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=self.kwargs.get('gid'))
        if not request.user.has_perm('group_app.can_view_group', group):
            raise PermissionDenied
        self.group = group
        return super(AbonCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            'group': self.group,
            'address': _('Address'),
            'is_active': False
        }

    def get_context_data(self, **kwargs):
        context = super(AbonCreateView, self).get_context_data(**kwargs)
        context['group'] = self.group
        return context

    def form_valid(self, form):
        try:
            abon = form.save()
            me = self.request.user
            assign_perm("abonapp.change_abon", me, abon)
            assign_perm("abonapp.delete_abon", me, abon)
            assign_perm("abonapp.can_buy_tariff", me, abon)
            assign_perm("abonapp.can_view_passport", me, abon)
            assign_perm('abonapp.can_add_ballance', me, abon)
            abon.sync_with_nas(created=True)
            messages.success(self.request, _('create abon success msg'))
            self.abon = abon
            return super(AbonCreateView, self).form_valid(form)
        except (IntegrityError, NasFailedResult, NasNetworkError, mydefs.LogicError) as e:
            messages.error(self.request, e)
        except mydefs.MultipleException as errs:
            for err in errs.err_list:
                messages.error(self.request, err)
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        messages.error(self.request, _('fix form errors'))
        return super(AbonCreateView, self).form_invalid(form)


@login_required
@mydefs.only_admins
def del_abon(request):
    uid = request.GET.get('id')
    try:
        abon = get_object_or_404(models.Abon, pk=uid)
        if not request.user.has_perm('abonapp.delete_abon') or not request.user.has_perm(
                'group_app.can_view_group', abon.group):
            raise PermissionDenied
        gid = abon.group.id
        abon.delete()
        abon.sync_with_nas(created=False)
        messages.success(request, _('delete abon success msg'))
        return mydefs.res_success(request, resolve_url('abonapp:people_list', gid=gid))

    except NasNetworkError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, _("NAS says: '%s'") % e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
    return redirect('abonapp:group_list')


@login_required
@permission_required('abonapp.can_add_ballance')
@transaction.atomic
def abonamount(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    try:
        if request.method == 'POST':
            abonuname = request.POST.get('abonuname')
            if abonuname == uname:
                amnt = mydefs.safe_float(request.POST.get('amount'))
                abon.add_ballance(request.user, amnt, comment=_('fill account through admin side'))
                abon.save(update_fields=['ballance'])
                messages.success(request, _('Account filled successfully on %.2f') % amnt)
                return redirect('abonapp:abon_phistory', gid=gid, uname=uname)
            else:
                messages.error(request, _('I not know the account id'))
    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
    return render_to_text('abonapp/modal_abonamount.html', {
        'abon': abon,
        'group_id': gid
    }, request=request)


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
@method_decorator(permission_required('group_app.can_view_group', (Group, 'pk', 'gid')), name='dispatch')
class DebtsListView(BaseAbonListView):
    context_object_name = 'invoices'
    template_name = 'abonapp/invoiceForPayment.html'

    def get_queryset(self):
        abon = get_object_or_404(models.Abon, username=self.kwargs.get('uname'))
        self.abon = abon
        return models.InvoiceForPayment.objects.filter(abon=abon)

    def get_context_data(self, **kwargs):
        context = super(DebtsListView, self).get_context_data(**kwargs)
        context['group'] = self.abon.group
        context['abon'] = self.abon
        return context


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
@method_decorator(permission_required('group_app.can_view_group', (Group, 'pk', 'gid')), name='dispatch')
class PayHistoryListView(BaseAbonListView):
    context_object_name = 'pay_history'
    template_name = 'abonapp/payHistory.html'

    def get_queryset(self):
        abon = get_object_or_404(models.Abon, username=self.kwargs.get('uname'))
        self.abon = abon
        pay_history = models.AbonLog.objects.filter(abon=abon).order_by('-date')
        return pay_history

    def get_context_data(self, **kwargs):
        context = super(PayHistoryListView, self).get_context_data(**kwargs)
        context['group'] = self.abon.group
        context['abon'] = self.abon
        return context


@login_required
@mydefs.only_admins
def abon_services(request, gid, uname):
    grp = get_object_or_404(Group, pk=gid)
    if not request.user.has_perm('group_app.can_view_group', grp):
        raise PermissionDenied
    abon = get_object_or_404(models.Abon, username=uname)

    if abon.group != grp:
        messages.warning(request, _("User group id is not matches with group in url"))
        return redirect('abonapp:abon_services', abon.group.id, abon.username)

    try:
        periodic_pay = models.PeriodicPayForId.objects.get(account=abon)
    except models.PeriodicPayForId.DoesNotExist:
        periodic_pay = None

    return render(request, 'abonapp/service.html', {
        'abon': abon,
        'abon_tariff': abon.current_tariff,
        'group': abon.group,
        'services': Tariff.objects.get_tariffs_by_group(abon.group.pk),
        'periodic_pay': periodic_pay
    })


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
@method_decorator(permission_required('abonapp.change_abon'), name='post')
class AbonHomeUpdateView(UpdateView):
    model = models.Abon
    form_class = forms.AbonForm
    slug_field = 'username'
    slug_url_kwarg = 'uname'
    template_name = 'abonapp/editAbon.html'
    context_object_name = 'abon'
    group = None

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(AbonHomeUpdateView, self).dispatch(request, *args, **kwargs)
        except mydefs.LogicError as e:
            messages.error(request, e)
        except (NasFailedResult, NasNetworkError) as e:
            messages.error(request, e)
        except models.AbonRawPassword.DoesNotExist:
            messages.warning(request, _('User has not have password, and cannot login'))
        except mydefs.MultipleException as errs:
            for err in errs.err_list:
                messages.error(request, err)
        return self.render_to_response(self.get_context_data())

    def get_object(self, queryset=None):
        gid = self.kwargs.get('gid')
        self.group = get_object_or_404(Group, pk=gid)
        if not self.request.user.has_perm('group_app.can_view_group', self.group):
            raise PermissionDenied
        return super(AbonHomeUpdateView, self).get_object(queryset)

    def form_valid(self, form):
        r = super(AbonHomeUpdateView, self).form_valid(form)
        abon = self.object
        res = abon.sync_with_nas(created=False)
        if isinstance(res, Exception):
            messages.warning(self.request, res)
        messages.success(self.request, _('edit abon success msg'))
        return r

    def form_invalid(self, form):
        messages.warning(self.request, _('fix form errors'))
        return super(AbonHomeUpdateView, self).form_invalid(form)

    def get(self, request, *args, **kwargs):
        r = super(AbonHomeUpdateView, self).get(request, *args, **kwargs)
        abon = self.object
        if abon.device is None:
            messages.warning(request, _('User device was not found'))
        return r

    def get_initial(self):
        abon = self.object
        passw = models.AbonRawPassword.objects.get(account=abon).passw_text
        return {
            'password': passw
        }

    def get_context_data(self, **kwargs):
        abon = self.object
        dev = getattr(abon, 'device')
        context = {
            'group': self.group,
            'is_bad_ip': getattr(abon, 'is_bad_ip', False),
            'device': dev,
            'dev_ports': DevPort.objects.filter(device=dev) if dev else None
        }
        context.update(kwargs)
        return super(AbonHomeUpdateView, self).get_context_data(**context)

    def get_success_url(self):
        abon = self.object
        return resolve_url('abonapp:abon_home',
            gid=getattr(abon.group, 'pk', 0),
            uname=abon.username
        )


@transaction.atomic
def terminal_pay(request):
    from .pay_systems import allpay
    ret_text = allpay(request)
    return HttpResponse(ret_text)


@login_required
@permission_required('abonapp.add_invoiceforpayment')
def add_invoice(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    grp = get_object_or_404(Group, pk=gid)

    try:
        if request.method == 'POST':
            curr_amount = mydefs.safe_int(request.POST.get('curr_amount'))
            comment = request.POST.get('comment')

            newinv = models.InvoiceForPayment()
            newinv.abon = abon
            newinv.amount = curr_amount
            newinv.comment = comment

            if request.POST.get('status') == 'on':
                newinv.status = True

            newinv.author = request.user
            newinv.save()
            messages.success(request, _('Receipt has been created'))
            return redirect('abonapp:abon_home', gid=gid, username=uname)

    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
    return render(request, 'abonapp/addInvoice.html', {
        'abon': abon,
        'invcount': models.InvoiceForPayment.objects.filter(abon=abon).count(),
        'group': grp
    })


@login_required
@mydefs.only_admins
@permission_required('abonapp.can_buy_tariff')
@transaction.atomic
def pick_tariff(request, gid, uname):
    grp = get_object_or_404(Group, pk=gid)
    abon = get_object_or_404(models.Abon, username=uname)
    tariffs = Tariff.objects.get_tariffs_by_group(grp.pk)
    try:
        if request.method == 'POST':
            trf = Tariff.objects.get(pk=request.POST.get('tariff'))
            deadline = request.POST.get('deadline')
            log_comment = _("Service '%(service_name)s' has connected via admin") % {
                'service_name': trf.title
            }
            if deadline == '' or deadline is None:
                abon.pick_tariff(trf, request.user, comment=log_comment)
            else:
                deadline = datetime.strptime(deadline, '%Y-%m-%d')
                deadline += timedelta(hours=23, minutes=59, seconds=59)
                abon.pick_tariff(trf, request.user, deadline=deadline, comment=log_comment)
            abon.sync_with_nas(created=False)
            messages.success(request, _('Tariff has been picked'))
            return redirect('abonapp:abon_services', gid=gid, uname=abon.username)
    except (mydefs.LogicError, NasFailedResult) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
        return redirect('abonapp:abon_services', gid=gid, uname=abon.username)
    except Tariff.DoesNotExist:
        messages.error(request, _('Tariff your picked does not exist'))
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
    except ValueError as e:
        messages.error(request, "%s: %s" % (_('fix form errors'), e))

    return render(request, 'abonapp/buy_tariff.html', {
        'tariffs': tariffs,
        'abon': abon,
        'group': grp,
        'selected_tariff': mydefs.safe_int(request.GET.get('selected_tariff'))
    })


@login_required
@permission_required('abonapp.delete_abontariff')
def unsubscribe_service(request, gid, uname, abon_tariff_id):
    try:
        abon = get_object_or_404(models.Abon, username=uname)
        abon_tariff = get_object_or_404(models.AbonTariff, pk=int(abon_tariff_id))
        abon.sync_with_nas(created=False)
        abon_tariff.delete()
        messages.success(request, _('User has been detached from service'))
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
    return redirect('abonapp:abon_services', gid=gid, uname=uname)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('abonapp.can_view_abonlog'), name='dispatch')
class LogListView(ListView):
    paginate_by = PAGINATION_ITEMS_PER_PAGE
    http_method_names = ['get']
    context_object_name = 'logs'
    template_name = 'abonapp/log.html'
    model = models.AbonLog


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('abonapp.can_view_invoiceforpayment'), name='dispatch')
class DebtorsListView(ListView):
    paginate_by = PAGINATION_ITEMS_PER_PAGE
    http_method_names = ['get']
    context_object_name = 'invoices'
    template_name = 'abonapp/debtors.html'
    queryset = models.InvoiceForPayment.objects.filter(status=True)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('group_app.can_view_group', (Group, 'pk', 'gid')), name='dispatch')
class TaskLogListView(ListView):
    paginate_by = PAGINATION_ITEMS_PER_PAGE
    http_method_names = ['get']
    context_object_name = 'tasks'
    template_name = 'abonapp/task_log.html'

    def get_queryset(self):
        abon = get_object_or_404(models.Abon, username=self.kwargs.get('uname'))
        self.abon = abon
        return Task.objects.filter(abon=abon)

    def get_context_data(self, **kwargs):
        context = super(TaskLogListView, self).get_context_data(**kwargs)
        context['group'] = self.abon.group
        context['abon'] = self.abon
        return context


@login_required
@permission_required('abonapp.can_view_passport')
def passport_view(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    try:
        if request.method == 'POST':
            try:
                passport_instance = models.PassportInfo.objects.get(abon=abon)
            except models.PassportInfo.DoesNotExist:
                passport_instance = None
            frm = forms.PassportForm(request.POST, instance=passport_instance)
            if frm.is_valid():
                pi = frm.save(commit=False)
                pi.abon = abon
                pi.save()
                messages.success(request, _('Passport information has been saved'))
                return redirect('abonapp:passport_view', gid=gid, uname=uname)
            else:
                messages.error(request, _('fix form errors'))
        else:
            passp_instance = models.PassportInfo.objects.get(abon=abon)
            frm = forms.PassportForm(instance=passp_instance)
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    except models.PassportInfo.DoesNotExist:
        messages.warning(request, _('Passport info for the user does not exist'))
        frm = forms.PassportForm()
    return render(request, 'abonapp/passport_view.html', {
        'group': get_object_or_404(Group, pk=gid),
        'abon': abon,
        'frm': frm
    })


@login_required
@mydefs.only_admins
def chgroup_tariff(request, gid):
    grp = get_object_or_404(Group, pk=gid)
    if not request.user.has_perm('group_app.change_group', grp):
        raise PermissionDenied
    if request.method == 'POST':
        tr = request.POST.getlist('tr')
        grp.tariff_set.clear()
        grp.tariff_set.add(*[int(d) for d in tr])
        grp.save()
        messages.success(request, _('Successfully saved'))
        return redirect('abonapp:ch_group_tariff', gid)
    tariffs = Tariff.objects.all()
    seleted_tariffs_id = [pk[0] for pk in grp.tariff_set.only('pk').values_list('pk')]
    return render(request, 'abonapp/group_tariffs.html', {
        'group': grp,
        'seleted_tariffs': seleted_tariffs_id,
        'tariffs': tariffs
    })


@login_required
@permission_required('abonapp.change_abon')
def dev(request, gid, uname):
    abon_dev = None
    try:
        abon = models.Abon.objects.get(username=uname)
        if request.method == 'POST':
            dev = Device.objects.get(pk=request.POST.get('dev'))
            abon.device = dev
            abon.save(update_fields=['device'])
            messages.success(request, _('Device has successfully attached'))
            return redirect('abonapp:abon_home', gid=gid, uname=uname)
        else:
            abon_dev = abon.device
    except Device.DoesNotExist:
        messages.warning(request, _('Device your selected already does not exist'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    return render(request, 'abonapp/modal_dev.html', {
        'devices': Device.objects.filter(group=gid),
        'dev': abon_dev,
        'gid': gid, 'uname': uname
    })


@login_required
@permission_required('abonapp.change_abon')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def clear_dev(request, gid, uname):
    try:
        abon = models.Abon.objects.get(username=uname)
        abon.device = None
        abon.dev_port = None
        abon.save(update_fields=['device', 'dev_port'])
        messages.success(request, _('Device has successfully unattached'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    return redirect('abonapp:abon_home', gid=gid, uname=uname)


@login_required
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def charts(request, gid, uname):
    high = 100

    wandate = request.GET.get('wantdate')
    if wandate:
        wandate = datetime.strptime(wandate, '%d%m%Y').date()
    else:
        wandate = date.today()

    try:
        StatElem = getModel(wandate)
        abon = models.Abon.objects.get(username=uname)
        if abon.group is None:
            abon.group = Group.objects.get(pk=gid)
            abon.save(update_fields=['group'])

        charts_data = StatElem.objects.chart(
            abon.username,
            count_of_parts=30,
            want_date=wandate
        )

        abontariff = abon.active_tariff()
        if abontariff is not None:
            trf = abontariff.tariff
            high = trf.speedIn + trf.speedOut
            if high > 100:
                high = 100

    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid)
    except Group.DoesNotExist:
        messages.error(request, _("Group what you want doesn't exist"))
        return redirect('abonapp:group_list')
    except ProgrammingError as e:
        messages.error(request, e)
        return redirect('abonapp:abon_home', gid=gid, uname=uname)

    return render(request, 'abonapp/charts.html', {
        'group': abon.group,
        'abon': abon,
        'charts_data': ',\n'.join(charts_data) if charts_data is not None else None,
        'high': high,
        'wantdate': wandate
    })


@login_required
@permission_required('abonapp.add_extrafieldsmodel')
def make_extra_field(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    try:
        if request.method == 'POST':
            frm = forms.ExtraFieldForm(request.POST)
            if frm.is_valid():
                field_instance = frm.save()
                abon.extra_fields.add(field_instance)
                messages.success(request, _('Extra field successfully created'))
            else:
                messages.error(request, _('fix form errors'))
            return redirect('abonapp:abon_home', gid=gid, username=uname)
        else:
            frm = forms.ExtraFieldForm()

    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
        frm = forms.ExtraFieldForm()
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.error(request, err)
        frm = forms.ExtraFieldForm()
    return render_to_text('abonapp/modal_extra_field.html', {
        'abon': abon,
        'gid': gid,
        'frm': frm
    }, request=request)


@login_required
@permission_required('abonapp.change_extra_fields_model')
def extra_field_change(request, gid, uname):
    extras = [(int(x), y) for x, y in zip(request.POST.getlist('ed'), request.POST.getlist('ex'))]
    try:
        for ex in extras:
            extra_field = models.ExtraFieldsModel.objects.get(pk=ex[0])
            extra_field.data = ex[1]
            extra_field.save(update_fields=['data'])
        messages.success(request, _("Extra fields has been saved"))
    except models.ExtraFieldsModel.DoesNotExist:
        messages.error(request, _('One or more extra fields has not been saved'))
    return redirect('abonapp:abon_home', gid=gid, username=uname)


@login_required
@permission_required('abonapp.delete_extra_fields_model')
def extra_field_delete(request, gid, uname, fid):
    abon = get_object_or_404(models.Abon, username=uname)
    try:
        extra_field = models.ExtraFieldsModel.objects.get(pk=fid)
        abon.extra_fields.remove(extra_field)
        extra_field.delete()
        messages.success(request, _('Extra field successfully deleted'))
    except models.ExtraFieldsModel.DoesNotExist:
        messages.warning(request, _('Extra field does not exist'))
    return redirect('abonapp:abon_home', gid=gid, uname=uname)


@login_required
@permission_required('abonapp.can_ping')
@json_view
def abon_ping(request):
    ip = request.GET.get('cmd_param')
    status = False
    text = '<span class="glyphicon glyphicon-exclamation-sign"></span> %s' % _('no ping')
    try:
        if ip is None:
            raise mydefs.LogicError(_('Ip not passed'))
        tm = Transmitter()
        ping_result = tm.ping(ip)
        if ping_result is None:
            if ping(ip, 10):
                status = True
                text = '<span class="glyphicon glyphicon-ok"></span> %s' % _('ping ok')
        else:
            if type(ping_result) is tuple:
                loses_percent = (ping_result[0] / ping_result[1] if ping_result[1] != 0 else 1)
                ping_result = {'all': ping_result[0], 'return': ping_result[1]}
                if loses_percent > 1.0:
                    text = '<span class="glyphicon glyphicon-exclamation-sign"></span> %s' % _(
                        'IP Conflict! %(all)d/%(return)d results') % ping_result
                elif loses_percent > 0.5:
                    text = '<span class="glyphicon glyphicon-ok"></span> %s' % _(
                        'ok ping, %(all)d/%(return)d loses') % ping_result
                    status = True
                else:
                    text = '<span class="glyphicon glyphicon-exclamation-sign"></span> %s' % _(
                        'no ping, %(all)d/%(return)d loses') % ping_result
            else:
                text = '<span class="glyphicon glyphicon-ok"></span> %s' % _('ping ok') + ' ' + str(ping_result)
                status = True

    except (NasFailedResult, mydefs.LogicError) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)

    return {
        'status': 0 if status else 1,
        'dat': text
    }


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
class DialsListView(BaseAbonListView):
    context_object_name = 'logs'
    template_name = 'abonapp/dial_log.html'

    def get_queryset(self):
        abon = get_object_or_404(models.Abon, username=self.kwargs.get('uname'))
        if not self.request.user.has_perm('group_app.can_view_group', abon.group):
            raise PermissionDenied
        self.abon = abon
        if abon.telephone is not None and abon.telephone != '':
            tel = abon.telephone.replace('+', '')
            logs = AsteriskCDR.objects.filter(
                Q(src__contains=tel) | Q(dst__contains=tel)
            )
            return logs
        else:
            return AsteriskCDR.objects.empty()

    def get_context_data(self, **kwargs):
        context = super(DialsListView, self).get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, pk=self.kwargs.get('gid'))
        context['abon'] = self.abon
        return context

    def render_to_response(self, context, **response_kwargs):
        if hasattr(self.abon.group, 'pk') and self.abon.group.pk != int(self.kwargs.get('gid')):
            return redirect('abonapp:dials', self.abon.group.pk, self.abon.username)
        return super(DialsListView, self).render_to_response(context, **response_kwargs)

    def get(self, request, *args, **kwargs):
        try:
            return super(DialsListView, self).get(request, *args, **kwargs)
        except ProgrammingError as e:
            messages.error(request, e)
            return redirect('abonapp:abon_home',
                            self.kwargs.get('gid'),
                            self.kwargs.get('uname'))


@login_required
@permission_required('abonapp.change_abon')
def save_user_dev_port(request, gid, uname):
    if request.method != 'POST':
        messages.error(request, _('Method is not POST'))
        return redirect('abonapp:abon_home', gid, uname)
    user_port = mydefs.safe_int(request.POST.get('user_port'))
    is_dynamic_ip = request.POST.get('is_dynamic_ip')
    is_dynamic_ip = True if is_dynamic_ip == 'on' else False
    try:
        abon = models.Abon.objects.get(username=uname)
        if user_port == 0:
            port = None
        else:
            port = DevPort.objects.get(pk=user_port)
            if abon.device is not None:
                try:
                    other_abon = models.Abon.objects.get(device=abon.device, dev_port=port)
                    if other_abon != abon:
                        user_url = resolve_url('abonapp:abon_home', other_abon.group.id, other_abon.username)
                        messages.error(request, _(
                            "<a href='%(user_url)s'>%(user_name)s</a> already pinned to this port on this device") % {
                                           'user_url': user_url,
                                           'user_name': other_abon.get_full_name()
                                       })
                        return redirect('abonapp:abon_home', gid, uname)
                except models.Abon.DoesNotExist:
                    pass
                except models.Abon.MultipleObjectsReturned:
                    messages.error(request, _('Multiple users on the same device port'))
                    return redirect('devapp:manage_ports', abon.device.group.pk, abon.device.pk)

        abon.dev_port = port
        if abon.is_dynamic_ip != is_dynamic_ip:
            abon.is_dynamic_ip = is_dynamic_ip
            abon.save(update_fields=['dev_port', 'is_dynamic_ip'])
        else:
            abon.save(update_fields=['dev_port'])
        messages.success(request, _('User port has been saved'))
    except DevPort.DoesNotExist:
        messages.error(request, _('Selected port does not exist'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('User does not exist'))
    return redirect('abonapp:abon_home', gid, uname)


@login_required
@permission_required('abonapp.add_abonstreet')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def street_add(request, gid):
    if request.method == 'POST':
        frm = forms.AbonStreetForm(request.POST)
        if frm.is_valid():
            frm.save()
            messages.success(request, _('Street successfully saved'))
            return redirect('abonapp:people_list', gid)
        else:
            messages.error(request, _('fix form errors'))
    else:
        frm = forms.AbonStreetForm(initial={'group': gid})
    return render_to_text('abonapp/modal_addstreet.html', {
        'form': frm,
        'gid': gid
    }, request=request)


@login_required
@permission_required('abonapp.change_abonstreet')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def street_edit(request, gid):
    try:
        if request.method == 'POST':
            streets_pairs = [(int(sid), sname) for sid, sname in
                             zip(request.POST.getlist('sid'), request.POST.getlist('sname'))]
            for sid, sname in streets_pairs:
                street = models.AbonStreet.objects.get(pk=sid)
                street.name = sname
                street.save()
            messages.success(request, _('Streets has been saved'))
        else:
            return render_to_text('abonapp/modal_editstreet.html', {
                'gid': gid,
                'streets': models.AbonStreet.objects.filter(group=gid)
            }, request=request)

    except models.AbonStreet.DoesNotExist:
        messages.error(request, _('One of these streets has not been found'))

    return redirect('abonapp:people_list', gid)


@login_required
@permission_required('abonapp.delete_abonstreet')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def street_del(request, gid, sid):
    try:
        models.AbonStreet.objects.get(pk=sid, group=gid).delete()
        messages.success(request, _('The street successfully deleted'))
    except models.AbonStreet.DoesNotExist:
        messages.error(request, _('The street has not been found'))
    return redirect('abonapp:people_list', gid)


@login_required
@permission_required('abonapp.can_view_additionaltelephones')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def tels(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    telephones = abon.additional_telephones.all()
    return render_to_text('abonapp/modal_additional_telephones.html', {
        'telephones': telephones,
        'gid': gid,
        'uname': uname
    }, request=request)


@login_required
@permission_required('abnapp.add_additionaltelephone')
def tel_add(request, gid, uname):
    if request.method == 'POST':
        frm = forms.AdditionalTelephoneForm(request.POST)
        if frm.is_valid():
            new_tel = frm.save(commit=False)
            abon = get_object_or_404(models.Abon, username=uname)
            new_tel.abon = abon
            new_tel.save()
            messages.success(request, _('New telephone has been saved'))
            return redirect('abonapp:abon_home', gid, uname)
        else:
            messages.error(request, _('fix form errors'))
    else:
        frm = forms.AdditionalTelephoneForm()
    return render_to_text('abonapp/modal_add_phone.html', {
        'form': frm,
        'gid': gid,
        'uname': uname
    }, request=request)


@login_required
@permission_required('abnapp.delete_additionaltelephone')
def tel_del(request, gid, uname):
    try:
        tid = mydefs.safe_int(request.GET.get('tid'))
        tel = models.AdditionalTelephone.objects.get(pk=tid)
        tel.delete()
        messages.success(request, _('Additional telephone successfully deleted'))
    except models.AdditionalTelephone.DoesNotExist:
        messages.error(request, _('Telephone not found'))
    return redirect('abonapp:abon_home', gid, uname)


@login_required
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def phonebook(request, gid):
    res_format = request.GET.get('f')
    t1 = models.Abon.objects.filter(group__id=int(gid)).only('telephone', 'fio').values_list('telephone', 'fio')
    t2 = models.AdditionalTelephone.objects.filter(abon__group__id=gid).only('telephone', 'owner_name').values_list(
        'telephone', 'owner_name')
    tels = list(t1) + list(t2)
    if res_format == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="phones.csv"'
        writer = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
        for row in tels:
            writer.writerow(row)
        return response
    return render_to_text('abonapp/modal_phonebook.html', {
        'tels': tels,
        'gid': gid
    }, request=request)


@login_required
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def abon_export(request, gid):
    res_format = request.GET.get('f')

    if request.method == 'POST':
        frm = forms.ExportUsersForm(request.POST)
        if frm.is_valid():
            cleaned_data = frm.clean()
            fields = cleaned_data.get('fields')
            subscribers = models.Abon.objects.filter(group__id=gid).only(*fields).values_list(*fields)
            if res_format == 'csv':
                import csv
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="users.csv"'
                writer = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
                display_values = [f[1] for f in frm.fields['fields'].choices if f[0] in fields]
                writer.writerow(display_values)
                for row in subscribers:
                    writer.writerow(row)
                return response
            else:
                messages.info(request, _('Unexpected format %(export_format)s') % {'export_format': res_format})
                return redirect('abonapp:group_list')
        else:
            messages.error(request, _('fix form errors'))
            return redirect('abonapp:group_list')
    else:
        frm = forms.ExportUsersForm()
    return render_to_text('abonapp/modal_export.html', {
        'gid': gid,
        'form': frm
    }, request=request)


@login_required
@permission_required('abonapp.change_abon')
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
@json_view
def reset_ip(request, gid, uname):
    abon = get_object_or_404(models.Abon, username=uname)
    abon.ip_address = None
    abon.save(update_fields=['ip_address'])
    return {
        'status': 0,
        'dat': "<span class='glyphicon glyphicon-refresh'></span>"
    }


@login_required
@mydefs.only_admins
def fin_report(request):
    q = models.AllTimePayLog.objects.by_days()
    res_format = request.GET.get('f')
    if res_format == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'
        writer = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
        for row in q:
            writer.writerow((row['summ'], row['pay_date'].strftime('%Y-%m-%d')))
        return response
    return render(request, 'abonapp/fin_report.html', {
        'logs': q
    })


@login_required
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
def add_edit_periodic_pay(request, gid, uname, periodic_pay_id=0):
    if periodic_pay_id == 0:
        if not request.user.has_perm('abonapp.add_periodicpayforid'):
            raise PermissionDenied
        periodic_pay_instance = models.PeriodicPayForId()
    else:
        if not request.user.has_perm('abonapp.change_periodicpayforid'):
            raise PermissionDenied
        periodic_pay_instance = get_object_or_404(models.PeriodicPayForId, pk=periodic_pay_id)
    if request.method == 'POST':
        frm = forms.PeriodicPayForIdForm(request.POST, instance=periodic_pay_instance)
        if frm.is_valid():
            abon = get_object_or_404(models.Abon, username=uname)
            inst = frm.save(commit=False)
            inst.account = abon
            inst.save()
            messages.success(request, _('Periodic pays has been designated'))
        else:
            messages.error(request, _('Something wrong in form'))
        return redirect('abonapp:abon_services', gid, uname)
    else:
        frm = forms.PeriodicPayForIdForm(instance=periodic_pay_instance)
    return render_to_text('abonapp/modal_periodic_pay.html', {
        'form': frm,
        'gid': gid,
        'uname': uname
    }, request=request)


@login_required
@permission_required('group_app.can_view_group', (Group, 'pk', 'gid'))
@permission_required('abonapp.delete_periodicpayforid')
def del_periodic_pay(request, gid, uname, periodic_pay_id):
    periodic_pay_instance = get_object_or_404(models.PeriodicPayForId, pk=periodic_pay_id)
    if periodic_pay_instance.account.username != uname:
        uname = periodic_pay_instance.account.username
    periodic_pay_instance.delete()
    messages.success(request, _('Periodic pay successfully deleted'))
    return redirect('abonapp:abon_services', gid, uname)


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
class EditSibscriberMarkers(UpdateView):
    http_method_names = ['get', 'post']
    template_name = 'abonapp/modal_user_markers.html'
    form_class = forms.MarkersForm

    def get_object(self, queryset=None):
        obj = models.Abon.objects.get(username=self.kwargs.get('uname'))
        return obj

    def get_success_url(self):
        return resolve_url('abonapp:abon_home', self.kwargs.get('gid'), self.kwargs.get('uname'))

    def get_context_data(self, **kwargs):
        context = super(EditSibscriberMarkers, self).get_context_data(**kwargs)
        context['gid'] = self.kwargs.get('gid')
        context['uname'] = self.kwargs.get('uname')
        return context

    def form_invalid(self, form):
        messages.error(self.request, _('fix form errors'))
        return super(EditSibscriberMarkers, self).form_invalid(form)

    def form_valid(self, form):
        v = super(EditSibscriberMarkers, self).form_valid(form)
        messages.success(self.request, _('User flags has changed successfully'))
        return v


# API's
@login_required
@mydefs.only_admins
@json_view
def abons(request):
    ablist = [{
        'id': abn.pk,
        'tarif_id': abn.active_tariff().tariff.pk if abn.active_tariff() is not None else 0,
        'ip': abn.ip_address.int_ip(),
        'is_active': abn.is_active
    } for abn in models.Abon.objects.all()]

    tarlist = [{
        'id': trf.pk,
        'speedIn': trf.speedIn,
        'speedOut': trf.speedOut
    } for trf in Tariff.objects.all()]

    data = {
        'subscribers': ablist,
        'tariffs': tarlist
    }
    del ablist, tarlist
    return data


@login_required
@mydefs.only_admins
@json_view
def search_abon(request):
    word = request.GET.get('s')
    if not word:
        return None
    results = models.Abon.objects.filter(fio__icontains=word)[:8]
    results = [{'id': usr.pk, 'text': "%s: %s" % (usr.username, usr.fio)} for usr in results]
    return results


class DhcpLever(SecureApiView):
    #
    # Api view for dhcp event
    #
    http_method_names = ['get']

    @method_decorator(json_view)
    def get(self, request, *args, **kwargs):
        data = request.GET.copy()
        r = self.on_dhcp_event(data)
        if r is not None:
            return {'text': r}
        return {'status': 'ok'}

    @staticmethod
    def on_dhcp_event(data: Dict) -> Optional[str]:
        '''
        data = {
            'client_ip': ip2int('127.0.0.1'),
            'client_mac': 'aa:bb:cc:dd:ee:ff',
            'switch_mac': 'aa:bb:cc:dd:ee:ff',
            'switch_port': 3,
            'cmd': 'commit'
        }
        '''
        r = None
        try:
            action = data['cmd']
            if action == 'commit':
                r = dhcp_commit(
                    data['client_ip'], data['client_mac'],
                    data['switch_mac'], data['switch_port']
                )
            elif action == 'expiry':
                r = dhcp_expiry(data['client_ip'])
            elif action == 'release':
                r = dhcp_release(data['client_ip'])
        except mydefs.LogicError as e:
            print('LogicError', e)
            r = str(e)
        return r
