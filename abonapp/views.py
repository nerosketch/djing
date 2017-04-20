# -*- coding: utf-8 -*-
from json import dumps
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied, MultipleObjectsReturned
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from tariff_app.models import Tariff
from agent import NasFailedResult, Transmitter, NasNetworkError
from . import forms
from . import models
from ip_pool.models import IpPoolItem
import mydefs
from devapp.models import Device
from datetime import datetime


@login_required
@mydefs.only_admins
def peoples(request, gid):
    street_id = mydefs.safe_int(request.GET.get('street'))
    if street_id > 0:
        peoples_list = models.Abon.objects.filter(group=gid, street=street_id)
    else:
        peoples_list = models.Abon.objects.filter(group=gid)

    # фильтр
    dr, field = mydefs.order_helper(request)
    if field:
        peoples_list = peoples_list.order_by(field)

    peoples_list = mydefs.pag_mn(request, peoples_list)

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
                frm.save()
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
@permission_required('abonapp.delete_abongroup')
def delgroup(request):
    try:
        agd = mydefs.safe_int(request.GET.get('id'))
        get_object_or_404(models.AbonGroup, pk=agd).delete()
        messages.success(request, _('delete group success msg'))
        return mydefs.res_success(request, 'abonapp:group_list')
    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return mydefs.res_error(request, 'abonapp:group_list')


@login_required
@permission_required('abonapp.add_abon')
def addabon(request, gid):
    frm = None
    group = None
    try:
        group = get_object_or_404(models.AbonGroup, pk=gid)
        if request.method == 'POST':
            frm = forms.AbonForm(request.POST, initial={'group': group})
            if frm.is_valid():
                abon = frm.save()
                messages.success(request, _('create abon success msg'))
                return redirect('abonapp:abon_home', group.id, abon.pk)
            else:
                messages.error(request, _('fix form errors'))

    except (IntegrityError, NasFailedResult, NasNetworkError, models.LogicError) as e:
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
def delentity(request):
    typ = request.GET.get('t')
    uid = request.GET.get('id')
    try:
        if typ == 'a':
            if not request.user.has_perm('abonapp.delete_abon'):
                raise PermissionDenied
            abon = get_object_or_404(models.Abon, pk=uid)
            gid = abon.group.id
            abon.delete()
            messages.success(request, _('delete abon success msg'))
            return mydefs.res_success(request, resolve_url('abonapp:people_list', gid=gid))
        elif typ == 'g':
            if not request.user.has_perm('abonapp.delete_abongroup'):
                raise PermissionDenied
            get_object_or_404(models.AbonGroup, pk=uid).delete()
            messages.success(request, _('delete group success msg'))
            return mydefs.res_success(request, 'abonapp:group_list')
        else:
            messages.warning(request, _('I not know what to delete'))
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
    abon = get_object_or_404(models.Abon, pk=uid)
    abon_tarifs = models.AbonTariff.objects.filter(abon=uid)

    active_abontariff = abon_tarifs.exclude(time_start=None)

    return render(request, 'abonapp/services.html', {
        'abon': abon,
        'abon_tarifs': abon_tarifs,
        'active_abontariff_id': active_abontariff[0].id if active_abontariff.count() > 0 else None,
        'abon_group': abon.group
    })


@login_required
@mydefs.only_admins
def abonhome(request, gid, uid):
    abon = get_object_or_404(models.Abon, pk=uid)
    abon_group = get_object_or_404(models.AbonGroup, pk=gid)
    frm = None
    passw = None
    abon_device = None
    try:
        if request.method == 'POST':
            if not request.user.has_perm('abonapp.change_abon'):
                raise PermissionDenied
            frm = forms.AbonForm(request.POST, instance=abon)
            if frm.is_valid():
                # если нет option82, т.е. динамический ip то не сохраняем изменения ip
                if abon.opt82 is None:
                    ip_str = request.POST.get('ip')
                    if ip_str:
                        try:
                            ip = IpPoolItem.objects.get(ip=ip_str)
                            abon.ip_address = ip
                        except MultipleObjectsReturned:
                            ips = models.IpPoolItem.objects.filter(ip=ip_str)
                            one_ip = ips[0]
                            models.IpPoolItem.objects.filter(pk__in=[ip.pk for ip in ips if ip != one_ip]).delete()
                            abon.ip_address = one_ip
                    else:
                        abon.ip_address = None
                frm.save()
                messages.success(request, _('edit abon success msg'))
            else:
                messages.warning(request, _('fix form errors'))
        else:
            passw = models.AbonRawPassword.objects.get(account=abon).passw_text
            frm = forms.AbonForm(instance=abon, initial={'password': passw})
            abon_device = models.AbonDevice.objects.get(abon=abon)
    except IntegrityError as e:
        messages.error(request, _('Ip address already exist. %s') % e)
        frm = forms.AbonForm(instance=abon, initial={'password': passw})

    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except IpPoolItem.DoesNotExist:
        messages.error(request, _('Ip address not found'))
    except models.AbonRawPassword.DoesNotExist:
        messages.warning(request, _('User has not have password, and cannot login'))
    except models.AbonDevice.DoesNotExist:
        messages.warning(request, _('User device was not found'))
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)

    if request.user.has_perm('abonapp.change_abon'):
        return render(request, 'abonapp/editAbon.html', {
            'form': frm or forms.AbonForm(instance=abon, initial={'password': passw}),
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address,
            'tech_form': forms.Opt82Form(instance=abon.opt82),
            'device': abon_device.device if abon_device is not None else None
        })
    else:
        return render(request, 'abonapp/viewAbon.html', {
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address,
            'passw': passw
        })


@login_required
@mydefs.only_admins
def opt82(request, gid, uid):
    try:
        abon = models.Abon.objects.get(pk=uid)
        if request.method == 'POST':
            try:
                opt82_instance = models.Opt82.objects.get(
                    mac=request.POST.get('mac'),
                    port=request.POST.get('port')
                )
            except models.Opt82.DoesNotExist:
                frm = forms.Opt82Form(request.POST)
                if frm.is_valid():
                    opt82_instance = frm.save()
                else:
                    messages.error(request, _('fix form errors'))
                    return redirect('abonapp:abon_home', gid=gid, uid=uid)

            abon.opt82 = opt82_instance
        else:
            act = request.GET.get('act')
            if act is not None and act == 'release':
                if abon.opt82 is not None:
                    abon.opt82.delete()
                    abon.opt82 = None

        abon.save(update_fields=['opt82'])
    except models.Abon.DoesNotExist:
        messages.error(request, _('User does not exist'))
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@mydefs.require_ssl
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
                abon.pick_tariff(trf, request.user, deadline=deadline)
            messages.success(request, _('Tariff has been picked'))
            return redirect('abonapp:abon_services', gid=gid, uid=abon.id)
    except (models.LogicError, NasFailedResult) as e:
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
        'abon_group': grp
    })


@login_required
@mydefs.only_admins
def chpriority(request, gid, uid):
    t = request.GET.get('t')
    act = request.GET.get('a')

    current_abon_tariff = get_object_or_404(models.AbonTariff, pk=t)

    try:
        if act == 'up':
            current_abon_tariff.priority_up()
        elif act == 'down':
            current_abon_tariff.priority_down()
    except (NasFailedResult, NasNetworkError) as e:
        messages.error(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)

    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.can_complete_service')
def complete_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, pk=srvid)
    abon = abtar.abon
    # считаем не использованные ресурсы
    calc_obj = abtar.tariff.get_calc_type()(abtar)
    # получаем сколько использовано
    res_amount = calc_obj.calc_amount()
    cashback = abtar.tariff.amount - res_amount

    if abtar.abon.group is None:
        abon.group = get_object_or_404(models.AbonGroup, pk=gid)
        abon.save(update_fields=['group'])
    if int(abtar.abon.pk) != int(uid) or int(abtar.abon.group.pk) != int(gid):
        # если что-то написали в урле вручную, то вернём на путь истинный
        return redirect('abonapp:compl_srv', gid=abtar.abon.group.pk, uid=abtar.abon.pk, srvid=srvid)
    time_use = None
    try:
        if request.method == 'POST':
            # досрочно завершаем услугу
            if request.POST.get('finish_confirm') == 'yes':
                if cashback > 0.5:
                    # возвращаем деньги, которые абонент не использовал
                    abon.add_ballance(
                        request.user,
                        cashback,
                        _('Refunds for unused resources')
                    )
                    abon.save(update_fields=['ballance'])

                # удаляем запись о текущей услуге.
                abtar.delete()
                messages.success(request, _('Service has been finished successfully'))
                return redirect('abonapp:abon_services', gid, uid)
            else:
                raise models.LogicError(_('Not confirmed'))

        time_use = mydefs.RuTimedelta(timezone.now() - abtar.time_start)

    except (models.LogicError, NasFailedResult) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
        return redirect('abonapp:abon_home', gid, uid)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)

    return render(request, 'abonapp/complete_service.html', {
        'abtar': abtar,
        'abon': abon,
        'time_use': time_use,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'tcost': round(res_amount, 4),
        'cashback': round(cashback, 4)
    })


@login_required
@permission_required('abonapp.can_activate_service')
def activate_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, pk=srvid)
    amount = abtar.calc_amount_service()

    try:
        if request.method == 'POST':
            if request.POST.get('finish_confirm') != 'yes':
                return HttpResponse(_('Not confirmed'))

            abtar.activate(request.user)
            messages.success(request, _('Service has been activated successfully'))
            return redirect('abonapp:abon_services', gid, uid)

    except (NasFailedResult, models.LogicError) as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    calc_obj = abtar.tariff.get_calc_type()(abtar)
    return render(request, 'abonapp/activate_service.html', {
        'abon': abtar.abon,
        'abon_group': abtar.abon.group,
        'abtar': abtar,
        'amount': amount,
        'diff': abtar.abon.ballance - amount,
        'deadline': calc_obj.calc_deadline()
    })


@login_required
@permission_required('abonapp.delete_abontariff')
def unsubscribe_service(request, gid, uid, srvid):
    try:
        get_object_or_404(models.AbonTariff, pk=int(srvid)).delete()
        messages.success(request, _('User has been detached from service'))
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@mydefs.only_admins
def log_page(request):
    logs = models.AbonLog.objects.all()
    logs = mydefs.pag_mn(request, logs)
    return render(request, 'abonapp/log.html', {
        'logs': logs
    })


@login_required
@mydefs.only_admins
def debtors(request):
    # peoples_list = models.Abon.objects.filter(invoiceforpayment__status=True)
    #peoples_list = mydefs.pag_mn(request, peoples_list)
    invs = models.InvoiceForPayment.objects.filter(status=True)
    invs = mydefs.pag_mn(request, invs)
    return render(request, 'abonapp/debtors.html', {
        #'peoples': peoples_list
        'invoices': invs
    })

@login_required
@mydefs.only_admins
def update_nas(request, group_id):
    users = models.Abon.objects.filter(group=group_id)
    try:
        tm = Transmitter()
        for usr in users:
            if not usr.ip_address:
                continue
            agent_abon = usr.build_agent_struct()
            if agent_abon is not None:
                tm.update_user(agent_abon)
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except mydefs.MultipleException as errs:
        for err in errs.err_list:
            messages.add_message(request, messages.constants.ERROR, err)
    return redirect('abonapp:people_list', gid=group_id)


@login_required
@mydefs.only_admins
def task_log(request, gid, uid):
    from taskapp.models import Task
    abon = get_object_or_404(models.Abon, pk=uid)
    tasks = Task.objects.filter(abon=abon)
    return render(request, 'abonapp/task_log.html', {
        'tasks': tasks,
        'abon_group': get_object_or_404(models.AbonGroup, pk=gid),
        'abon': abon
    })


@login_required
@mydefs.only_admins
def passport_view(request, gid, uid):
    try:
        abon = models.Abon.objects.get(pk=uid)
        if request.method == 'POST':
            frm = forms.PassportForm(request.POST)
            if frm.is_valid():
                passp_instance = frm.save(commit=False)
                passp_instance.abon = abon
                passp_instance.save()
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
@mydefs.only_admins
def dev(request, gid, uid):
    abon_dev = None
    try:
        if request.method == 'POST':
            dev = Device.objects.get(pk=request.POST.get('dev'))
            abon = models.Abon.objects.get(pk=uid)
            try:
                models.AbonDevice.objects.get(device=dev, abon=abon)
            except models.AbonDevice.DoesNotExist:
                models.AbonDevice.objects.create(abon=abon, device=dev)
                messages.success(request, _('Device has successfully attached'))
            return redirect('abonapp:abon_home', gid=gid, uid=uid)
        else:
            abon_dev = models.AbonDevice.objects.get(abon=uid).device
    except Device.DoesNotExist:
        messages.warning(request, _('Device your selected already does not exist'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    except models.AbonDevice.DoesNotExist:
        messages.warning(request, _('User device was not found'))
    return render(request, 'abonapp/modal_dev.html', {
        'devices': Device.objects.filter(user_group=gid),
        'dev': abon_dev,
        'gid': gid, 'uid': uid
    })


@login_required
@mydefs.only_admins
def clear_dev(request, gid, uid):
    try:
        abon = models.Abon.objects.get(pk=uid)
        abdev = models.AbonDevice.objects.get(abon=abon)
        abdev.delete()
        messages.success(request, _('Device has successfully unattached'))
    except models.Abon.DoesNotExist:
        messages.error(request, _('Abon does not exist'))
        return redirect('abonapp:people_list', gid=gid)
    return redirect('abonapp:abon_home', gid=gid, uid=uid)


# API's

def abons(request):
    ablist = [{
        'id': abn.pk,
        'tarif_id': abn.active_tariff().pk if abn.active_tariff() else 0,
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
    results = [{'id':usr.pk, 'name':usr.username, 'fio':usr.fio} for usr in results]
    return HttpResponse(dumps(results, ensure_ascii=False))
