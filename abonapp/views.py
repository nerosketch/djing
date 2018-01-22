# -*- coding: utf-8 -*-
from json import dumps
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, ProgrammingError
from django.db.models import Count, Q, signals
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

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
from guardian.shortcuts import get_objects_for_user, assign_perm
from guardian.decorators import permission_required_or_403 as permission_required


@login_required
@mydefs.only_admins
def peoples(request, gid):
    abon_group = get_object_or_404(models.AbonGroup, pk=gid)
    if not request.user.has_perm('abonapp.can_view_abongroup', abon_group):
        raise PermissionDenied
    street_id = mydefs.safe_int(request.GET.get('street'))
    peoples_list = models.Abon.objects.select_related('group', 'street')
    if street_id > 0:
        peoples_list = peoples_list.filter(group=abon_group, street=street_id)
    else:
        peoples_list = peoples_list.filter(group=abon_group)

    # фильтр
    dr, field = mydefs.order_helper(request)
    if field:
        peoples_list = peoples_list.order_by(field)

    try:
        peoples_list = mydefs.pag_mn(request, peoples_list)
        for abon in peoples_list:
            if abon.ip_address is not None:
                try:
                    abon.stat_cache = StatCache.objects.get(ip=abon.ip_address)
                except StatCache.DoesNotExist:
                    pass

    except mydefs.LogicError as e:
        messages.warning(request, e)

    streets = models.AbonStreet.objects.filter(group=gid)

    return render(request, 'abonapp/peoples.html', {
        'peoples': peoples_list,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'streets': streets,
        'street_id': street_id,
        'dir': dr,
        'order_by': request.GET.get('order_by')
    })


@login_required
@permission_required('abonapp.add_abongroup')
def addgroup(request):
    frm = forms.AbonGroupForm()
    try:
        if request.method == 'POST':
            frm = forms.AbonGroupForm(request.POST)
            if frm.is_valid():
                grp = frm.save()
                assign_perm('abonapp.can_view_abongroup', request.user, grp)
                assign_perm('abonapp.delete_abongroup', request.user, grp)
                assign_perm('abonapp.change_abongroup', request.user, grp)
                messages.success(request, _('create group success msg'))
                return redirect('abonapp:group_list')
            else:
                messages.error(request, _('fix form errors'))
    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return render(request, 'abonapp/addGroup.html', {
        'form': frm
    })


@login_required
@mydefs.only_admins
def grouplist(request):
    groups = models.AbonGroup.objects.annotate(usercount=Count('abon')).order_by('title')
    groups = get_objects_for_user(request.user, 'abonapp.can_view_abongroup', klass=groups, accept_global_perms=False)

    # фильтр
    directory, field = mydefs.order_helper(request)
    if field:
        groups = groups.order_by(field)

    groups = mydefs.pag_mn(request, groups)

    return render(request, 'abonapp/group_list.html', {
        'groups': groups,
        'dir': directory,
        'order_by': request.GET.get('order_by')
    })


@login_required
def delgroup(request):
    try:
        agd = mydefs.safe_int(request.GET.get('id'))
        abon_group = models.AbonGroup.objects.get(pk=agd)
        if not request.user.has_perm('abonapp.delete_abongroup', abon_group):
            raise PermissionDenied
        abon_group.delete()
        messages.success(request, _('delete group success msg'))
        return mydefs.res_success(request, 'abonapp:group_list')
    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except models.AbonGroup.DoesNotExist:
        return mydefs.res_error(request, 'Group with id=%d does not exist' % agd)
    return mydefs.res_error(request, 'abonapp:group_list')


@login_required
@permission_required('abonapp.add_abon')
def addabon(request, gid):
    frm = None
    group = None
    try:
        group = get_object_or_404(models.AbonGroup, pk=gid)
        if not request.user.has_perm('abonapp.can_view_abongroup', group):
            raise PermissionDenied
        if request.method == 'POST':
            frm = forms.AbonForm(request.POST, initial={'group': group})
            if frm.is_valid():
                abon = frm.save()
                assign_perm("abonapp.change_abon", request.user, abon)
                assign_perm("abonapp.delete_abon", request.user, abon)
                assign_perm("abonapp.can_buy_tariff", request.user, abon)
                assign_perm("abonapp.can_view_passport", request.user, abon)
                assign_perm('abonapp.can_add_ballance', request.user, abon)
                messages.success(request, _('create abon success msg'))
                return redirect('abonapp:abon_home', group.id, abon.pk)
            else:
                messages.error(request, _('fix form errors'))

    except (IntegrityError, NasFailedResult, NasNetworkError, mydefs.LogicError) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)

    if not frm:
        frm = forms.AbonForm(initial={
            'group': group,
            'address': _('Address'),
            'is_active': False
        })

    return render(request, 'abonapp/addAbon.html', {
        'form': frm,
        'abon_group': group
    })


@login_required
@mydefs.only_admins
def del_abon(request):
    uid = request.GET.get('id')
    try:
        abon = get_object_or_404(models.Abon, pk=uid)
        if not request.user.has_perm('abonapp.delete_abon') or not request.user.has_perm(
                'abonapp.can_view_abongroup', abon.group):
            raise PermissionDenied
        gid = abon.group.id
        abon.delete()
        messages.success(request, _('delete abon success msg'))
        return mydefs.res_success(request, resolve_url('abonapp:people_list', gid=gid))

    except NasNetworkError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, _("NAS says: '%s'") % e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return redirect('abonapp:group_list')


@login_required
@permission_required('abonapp.can_add_ballance')
@transaction.atomic
def abonamount(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    try:
        if request.method == 'POST':
            abonid = mydefs.safe_int(request.POST.get('abonid'))
            if abonid == int(uid):
                amnt = mydefs.safe_float(request.POST.get('amount'))
                abon.add_ballance(request.user, amnt, comment=_('fill account through admin side'))
                abon.save(update_fields=['ballance'])
                messages.success(request, _('Account filled successfully on %.2f') % amnt)
                return redirect('abonapp:abon_phistory', gid=gid, uid=uid)
            else:
                messages.error(request, _('I not know the account id'))
    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return render_to_text('abonapp/modal_abonamount.html', {
        'abon': abon,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid)
    }, request=request)


@login_required
@mydefs.only_admins
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def invoice_for_payment(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    invoices = models.InvoiceForPayment.objects.filter(abon=abon)
    invoices = mydefs.pag_mn(request, invoices)
    return render(request, 'abonapp/invoiceForPayment.html', {
        'invoices': invoices,
        'abon_group': abon.group,
        'abon': abon
    })


@login_required
@mydefs.only_admins
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def pay_history(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    pay_history = models.AbonLog.objects.filter(abon=abon).order_by('-id')
    pay_history = mydefs.pag_mn(request, pay_history)
    return render(request, 'abonapp/payHistory.html', {
        'pay_history': pay_history,
        'abon_group': abon.group,
        'abon': abon
    })


@login_required
@mydefs.only_admins
def abon_services(request, gid, uid):
    grp = get_object_or_404(models.AbonGroup, pk=gid)
    if not request.user.has_perm('abonapp.can_view_abongroup', grp):
        raise PermissionDenied
    abon = get_object_or_404(models.Abon, pk=uid)

    if abon.group != grp:
        messages.warning(request, _("User group id is not matches with group in url"))
        return redirect('abonapp:abon_services', abon.group.id, abon.id)

    try:
        periodic_pay = models.PeriodicPayForId.objects.get(account=abon)
    except models.PeriodicPayForId.DoesNotExist:
        periodic_pay = None

    return render(request, 'abonapp/service.html', {
        'abon': abon,
        'abon_tariff': abon.current_tariff,
        'abon_group': abon.group,
        'services': grp.tariffs.all(),
        'periodic_pay': periodic_pay
    })


@login_required
@mydefs.only_admins
def abonhome(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    abon_group = get_object_or_404(models.AbonGroup, pk=gid)
    if not request.user.has_perm('abonapp.can_view_abongroup', abon_group):
        raise PermissionDenied
    frm = None
    passw = None
    try:
        if request.method == 'POST':
            if not request.user.has_perm('abonapp.change_abon'):
                raise PermissionDenied
            frm = forms.AbonForm(request.POST, instance=abon)
            if frm.is_valid():
                newip = request.POST.get('ip')
                if newip:
                    abon.ip_address = newip
                frm.save()
                messages.success(request, _('edit abon success msg'))
            else:
                messages.warning(request, _('fix form errors'))
        else:
            passw = models.AbonRawPassword.objects.get(account=abon).passw_text
            frm = forms.AbonForm(instance=abon, initial={'password': passw})
            if abon.device is None:
                messages.warning(request, _('User device was not found'))
    except mydefs.LogicError as e:
        messages.error(request, e)
        passw = models.AbonRawPassword.objects.get(account=abon).passw_text
        frm = forms.AbonForm(instance=abon, initial={'password': passw})

    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except models.AbonRawPassword.DoesNotExist:
        messages.warning(request, _('User has not have password, and cannot login'))
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)

    if request.user.has_perm('abonapp.change_abon'):
        return render(request, 'abonapp/editAbon.html', {
            'form': frm or forms.AbonForm(instance=abon, initial={'password': passw}),
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address,
            'is_bad_ip': getattr(abon, 'is_bad_ip', False),
            'device': abon.device,
            'dev_ports': DevPort.objects.filter(device=abon.device) if abon.device else None
        })
    else:
        return render(request, 'abonapp/viewAbon.html', {
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address,
            'passw': passw
        })


@transaction.atomic
def terminal_pay(request):
    from .pay_systems import allpay
    ret_text = allpay(request)
    return HttpResponse(ret_text)


@login_required
@permission_required('abonapp.add_invoiceforpayment')
def add_invoice(request, gid, uid):
    uid = mydefs.safe_int(uid)
    abon = get_object_or_404(models.Abon, pk=uid)
    grp = get_object_or_404(models.AbonGroup, pk=gid)

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
            return redirect('abonapp:abon_home', gid=gid, uid=uid)

    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return render(request, 'abonapp/addInvoice.html', {
        'abon': abon,
        'invcount': models.InvoiceForPayment.objects.filter(abon=abon).count(),
        'abon_group': grp
    })


@login_required
@permission_required('abonapp.can_buy_tariff')
@transaction.atomic
def pick_tariff(request, gid, uid):
    grp = get_object_or_404(models.AbonGroup, pk=gid)
    abon = get_object_or_404(models.Abon, pk=uid)
    tariffs = grp.tariffs.all()
    try:
        if request.method == 'POST':
            trf = Tariff.objects.get(pk=request.POST.get('tariff'))
            deadline = request.POST.get('deadline')
            if deadline == '' or deadline is None:
                abon.pick_tariff(trf, request.user)
            else:
                deadline = datetime.strptime(deadline, '%Y-%m-%d')
                deadline += timedelta(hours=23, minutes=59, seconds=59)
                abon.pick_tariff(trf, request.user, deadline=deadline)
            messages.success(request, _('Tariff has been picked'))
            return redirect('abonapp:abon_services', gid=gid, uid=abon.id)
    except (mydefs.LogicError, NasFailedResult) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
        return redirect('abonapp:abon_services', gid=gid, uid=abon.id)
    except Tariff.DoesNotExist:
        messages.error(request, _('Tariff your picked does not exist'))
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    except ValueError as e:
        messages.error(request, "%s: %s" % (_('fix form errors'), e))

    return render(request, 'abonapp/buy_tariff.html', {
        'tariffs': tariffs,
        'abon': abon,
        'abon_group': grp,
        'selected_tariff': mydefs.safe_int(request.GET.get('selected_tariff'))
    })


@login_required
@permission_required('abonapp.delete_abontariff')
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def unsubscribe_service(request, gid, uid, abon_tariff_id):
    try:
        abon_tariff = get_object_or_404(models.AbonTariff, pk=int(abon_tariff_id))
        abon_tariff.delete()
        messages.success(request, _('User has been detached from service'))
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return redirect('abonapp:abon_services', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.can_view_abonlog')
def log_page(request):
    logs = models.AbonLog.objects.all()
    logs = mydefs.pag_mn(request, logs)
    return render(request, 'abonapp/log.html', {
        'logs': logs
    })


@login_required
@permission_required('abonapp.can_view_invoiceforpayment')
def debtors(request):
    invs = models.InvoiceForPayment.objects.filter(status=True)
    invs = mydefs.pag_mn(request, invs)
    return render(request, 'abonapp/debtors.html', {
        'invoices': invs
    })


@login_required
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def task_log(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    tasks = Task.objects.filter(abon=abon)
    return render(request, 'abonapp/task_log.html', {
        'tasks': tasks,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'abon': abon
    })


@login_required
@permission_required('abonapp.can_view_passport')
def passport_view(request, gid, uid):
    try:
        abon = models.Abon.objects.get(pk=uid)
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
                return redirect('abonapp:passport_view', gid=gid, uid=uid)
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
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'abon': abon,
        'frm': frm
    })


@login_required
@mydefs.only_admins
def chgroup_tariff(request, gid):
    grp = get_object_or_404(models.AbonGroup, pk=gid)
    if not request.user.has_perm('abonapp.change_abongroup', grp):
        raise PermissionDenied
    if request.method == 'POST':
        tr = request.POST.getlist('tr')
        grp.tariffs.clear()
        grp.tariffs.add(*[int(d) for d in tr])
        grp.save()
    tariffs = Tariff.objects.all()
    return render(request, 'abonapp/group_tariffs.html', {
        'abon_group': grp,
        'tariffs': tariffs
    })


@login_required
@permission_required('abonapp.change_abon')
def dev(request, gid, uid):
    abon_dev = None
    try:
        abon = models.Abon.objects.get(pk=uid)
        if request.method == 'POST':
            dev = Device.objects.get(pk=request.POST.get('dev'))
            abon.device = dev
            abon.save(update_fields=['device'])
            messages.success(request, _('Device has successfully attached'))
            return redirect('abonapp:abon_home', gid=gid, uid=uid)
        else:
            abon_dev = abon.device
    except Device.DoesNotExist:
        messages.warning(request, _('Device your selected already does not exist'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    return render(request, 'abonapp/modal_dev.html', {
        'devices': Device.objects.filter(user_group=gid),
        'dev': abon_dev,
        'gid': gid, 'uid': uid
    })


@login_required
@permission_required('abonapp.change_abon')
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def clear_dev(request, gid, uid):
    try:
        abon = models.Abon.objects.get(pk=uid)
        abon.device = None
        abon.save(update_fields=['device'])
        messages.success(request, _('Device has successfully unattached'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def charts(request, gid, uid):
    high = 100

    wandate = request.GET.get('wantdate')
    if wandate:
        wandate = datetime.strptime(wandate, '%d%m%Y').date()
    else:
        wandate = date.today()

    try:
        StatElem = getModel(wandate)
        abon = models.Abon.objects.get(pk=uid)
        if abon.group is None:
            abon.group = models.AbonGroup.objects.get(pk=gid)
            abon.save(update_fields=['group'])
        abongroup = abon.group

        if abon.ip_address is None:
            charts_data = None
        else:
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
    except models.AbonGroup.DoesNotExist:
        messages.error(request, _("Group what you want doesn't exist"))
        return redirect('abonapp:group_list')
    except ProgrammingError as e:
        messages.error(request, e)
        return redirect('abonapp:abon_home', gid=gid, uid=uid)

    return render(request, 'abonapp/charts.html', {
        'abon_group': abongroup,
        'abon': abon,
        'charts_data': ',\n'.join(charts_data) if charts_data is not None else None,
        'high': high,
        'wantdate': wandate
    })


@login_required
@permission_required('abonapp.add_extrafieldsmodel')
def make_extra_field(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    try:
        if request.method == 'POST':
            frm = forms.ExtraFieldForm(request.POST)
            if frm.is_valid():
                field_instance = frm.save()
                abon.extra_fields.add(field_instance)
                messages.success(request, _('Extra field successfully created'))
            else:
                messages.error(request, _('fix form errors'))
            return redirect('abonapp:abon_home', gid=gid, uid=uid)
        else:
            frm = forms.ExtraFieldForm()

    except (NasNetworkError, NasFailedResult) as e:
        messages.error(request, e)
        frm = forms.ExtraFieldForm()
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
        frm = forms.ExtraFieldForm()
    return render_to_text('abonapp/modal_extra_field.html', {
        'abon': abon,
        'gid': gid,
        'frm': frm
    }, request=request)


@login_required
@permission_required('abonapp.change_extra_fields_model')
def extra_field_change(request, gid, uid):
    extras = [(int(x), y) for x, y in zip(request.POST.getlist('ed'), request.POST.getlist('ex'))]
    try:
        for ex in extras:
            extra_field = models.ExtraFieldsModel.objects.get(pk=ex[0])
            extra_field.data = ex[1]
            extra_field.save(update_fields=['data'])
        messages.success(request, _("Extra fields has been saved"))
    except models.ExtraFieldsModel.DoesNotExist:
        messages.error(request, _('One or more extra fields has not been saved'))
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.delete_extra_fields_model')
def extra_field_delete(request, gid, uid, fid):
    abon = get_object_or_404(models.Abon, pk=uid)
    try:
        extra_field = models.ExtraFieldsModel.objects.get(pk=fid)
        abon.extra_fields.remove(extra_field)
        extra_field.delete()
        messages.success(request, _('Extra field successfully deleted'))
    except models.ExtraFieldsModel.DoesNotExist:
        messages.warning(request, _('Extra field does not exist'))
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.can_ping')
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
            if mydefs.ping(ip, 10):
                status = True
                text = '<span class="glyphicon glyphicon-ok"></span> %s' % _('ping ok')
        else:
            if type(ping_result) is tuple:
                loses_percent = (ping_result[0] / ping_result[1] if ping_result[1] != 0 else 1)
                ping_result = {'all':ping_result[0], 'return': ping_result[1]}
                if loses_percent > 1.0:
                    text = '<span class="glyphicon glyphicon-exclamation-sign"></span> %s' % _('IP Conflict! %(all)d/%(return)d results') % ping_result
                elif loses_percent > 0.5:
                    text = '<span class="glyphicon glyphicon-ok"></span> %s' % _('ok ping, %(all)d/%(return)d loses') % ping_result
                    status = True
                else:
                    text = '<span class="glyphicon glyphicon-exclamation-sign"></span> %s' % _('no ping, %(all)d/%(return)d loses') % ping_result
            else:
                text = '<span class="glyphicon glyphicon-ok"></span> %s' % _('ping ok') + ' ' + str(ping_result)
                status = True

    except (NasFailedResult, mydefs.LogicError) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)

    return HttpResponse(dumps({
        'status': 0 if status else 1,
        'dat': text
    }))


@login_required
@mydefs.only_admins
def dials(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    if not request.user.has_perm('abonapp.can_view_abongroup', abon.group):
        raise PermissionDenied
    if hasattr(abon.group, 'pk') and abon.group.pk != int(gid):
        return redirect('abonapp:dials', abon.group.pk, abon.pk)
    if abon.telephone is not None and abon.telephone != '':
        tel = abon.telephone.replace('+', '')
        logs = AsteriskCDR.objects.filter(
            Q(src__contains=tel) | Q(dst__contains=tel)
        )
        logs = mydefs.pag_mn(request, logs)
    else:
        logs = None
    return render(request, 'abonapp/dial_log.html', {
        'logs': logs,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'abon': abon
    })


@login_required
@permission_required('abonapp.change_abon')
def save_user_dev_port(request, gid, uid):
    if request.method != 'POST':
        messages.error(request, _('Method is not POST'))
        return redirect('abonapp:abon_home', gid, uid)
    user_port = mydefs.safe_int(request.POST.get('user_port'))
    is_dynamic_ip = request.POST.get('is_dynamic_ip')
    try:
        abon = models.Abon.objects.get(pk=uid)
        if user_port == 0:
            port = None
        else:
            port = DevPort.objects.get(pk=user_port)
            if abon.device is not None:
                try:
                    other_abon = models.Abon.objects.get(device=abon.device, dev_port=port)
                    user_url = resolve_url('abonapp:abon_home', other_abon.group.id, other_abon.id)
                    messages.error(request, _("<a href='%(user_url)s'>%(user_name)s</a> already pinned to this port on this device") % {
                        'user_url': user_url,
                        'user_name': other_abon.get_full_name()
                    })
                    return redirect('abonapp:abon_home', gid, uid)
                except models.Abon.DoesNotExist:
                    pass

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
    return redirect('abonapp:abon_home', gid, uid)


@login_required
@permission_required('abonapp.add_abonstreet')
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
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
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
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
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def street_del(request, gid, sid):
    try:
        models.AbonStreet.objects.get(pk=sid, group=gid).delete()
        messages.success(request, _('The street successfully deleted'))
    except models.AbonStreet.DoesNotExist:
        messages.error(request, _('The street has not been found'))
    return redirect('abonapp:people_list', gid)


@login_required
@permission_required('abonapp.can_view_additionaltelephones')
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def tels(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    telephones = abon.additional_telephones.all()
    return render_to_text('abonapp/modal_additional_telephones.html', {
        'telephones': telephones,
        'gid': gid,
        'uid': uid
    }, request=request)


@login_required
@permission_required('abnapp.add_additionaltelephone')
def tel_add(request, gid, uid):
    if request.method == 'POST':
        frm = forms.AdditionalTelephoneForm(request.POST)
        if frm.is_valid():
            new_tel = frm.save(commit=False)
            abon = get_object_or_404(models.Abon, pk=uid)
            new_tel.abon = abon
            new_tel.save()
            messages.success(request, _('New telephone has been saved'))
            return redirect('abonapp:abon_home', gid, uid)
        else:
            messages.error(request, _('fix form errors'))
    else:
        frm = forms.AdditionalTelephoneForm()
    return render_to_text('abonapp/modal_add_phone.html', {
        'form': frm,
        'gid': gid,
        'uid': uid
    }, request=request)


@login_required
@permission_required('abnapp.delete_additionaltelephone')
def tel_del(request, gid, uid):
    try:
        tid = mydefs.safe_int(request.GET.get('tid'))
        tel = models.AdditionalTelephone.objects.get(pk=tid)
        tel.delete()
        messages.success(request, _('Additional telephone successfully deleted'))
    except models.AdditionalTelephone.DoesNotExist:
        messages.error(request, _('Telephone not found'))
    return redirect('abonapp:abon_home', gid, uid)


@login_required
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def phonebook(request, gid):
    res_format = request.GET.get('f')
    t1 = models.Abon.objects.filter(group__id=int(gid)).only('telephone', 'fio').values_list('telephone', 'fio')
    t2 = models.AdditionalTelephone.objects.filter(abon__group__id=gid).only('telephone', 'owner_name').values_list('telephone', 'owner_name')
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
@permission_required('abonapp.change_abon')
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def reset_ip(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    signals.post_save.disconnect(models.abon_post_save, sender=models.Abon)
    abon.ip_address = None
    abon.save(update_fields=['ip_address'])
    signals.post_save.connect(models.abon_post_save, sender=models.Abon)
    return HttpResponse(dumps({
        'status': 0,
        'dat': "<span class='glyphicon glyphicon-refresh'></span>"
    }))


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
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
def add_edit_periodic_pay(request, gid, uid, periodic_pay_id=0):
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
            abon = get_object_or_404(models.Abon, pk=uid)
            inst = frm.save(commit=False)
            inst.account = abon
            inst.save()
            messages.success(request, _('Periodic pays has been designated'))
        else:
            messages.error(request, _('Something wrong in form'))
        return redirect('abonapp:abon_services', gid, uid)
    else:
        frm = forms.PeriodicPayForIdForm(instance=periodic_pay_instance)
    return render_to_text('abonapp/modal_periodic_pay.html', {
        'form': frm,
        'gid': gid,
        'uid': uid
    }, request=request)


@login_required
@permission_required('abonapp.can_view_abongroup', (models.AbonGroup, 'pk', 'gid'))
@permission_required('abonapp.delete_periodicpayforid')
def del_periodic_pay(request, gid, uid, periodic_pay_id):
    periodic_pay_instance = get_object_or_404(models.PeriodicPayForId, pk=periodic_pay_id)
    if periodic_pay_instance.account.id != uid:
        uid = periodic_pay_instance.account.id
    periodic_pay_instance.delete()
    messages.success(request, _('Periodic pay successfully deleted'))
    return redirect('abonapp:abon_services', gid, uid)



# API's

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
    return HttpResponse(dumps(data))


def search_abon(request):
    word = request.GET.get('s')
    results = models.Abon.objects.filter(fio__icontains=word)[:8]
    results = [{'id': usr.pk, 'text': "%s: %s" % (usr.username, usr.fio)} for usr in results]
    return HttpResponse(dumps(results, ensure_ascii=False))
