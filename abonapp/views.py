# -*- coding: utf-8 -*-
from json import dumps
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
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


@login_required
@mydefs.only_admins
def peoples(request, gid):
    peoples_list = models.Abon.objects.filter(group=gid)

    # фильтр
    dr, field = mydefs.order_helper(request)
    if field:
        peoples_list = peoples_list.order_by(field)

    peoples_list = mydefs.pag_mn(request, peoples_list)

    return render(request, 'abonapp/peoples.html', {
        'peoples': peoples_list,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
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
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
    return render(request, 'abonapp/addGroup.html', {
        'form': frm
    })


@login_required
@mydefs.only_admins
def grouplist(request):
    groups = models.AbonGroup.objects.annotate(usercount=Count('abon'))

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
        get_object_or_404(models.AbonGroup, id=agd).delete()
        messages.success(request, _('delete group success msg'))
        return mydefs.res_success(request, 'abonapp:group_list')
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
    return mydefs.res_error(request, 'abonapp:group_list')


@login_required
@permission_required('abonapp.add_abon')
def addabon(request, gid):
    frm = None
    group = None
    try:
        group = get_object_or_404(models.AbonGroup, id=gid)
        if request.method == 'POST':
            frm = forms.AbonForm(request.POST, initial={'group': group})
            if frm.is_valid():
                abon = frm.save()
                messages.success(request, _('create abon success msg'))
                return redirect('abonapp:abon_home', group.id, abon.pk)
            else:
                messages.error(request, _('fix form errors'))

    except IntegrityError as e:
        messages.error(request, e)
    except models.LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)

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
            abon = get_object_or_404(models.Abon, id=uid)
            gid = abon.group.id
            abon.delete()
            messages.success(request, _('delete abon success msg'))
            return mydefs.res_success(request, resolve_url('abonapp:people_list', gid=gid))
        elif typ == 'g':
            if not request.user.has_perm('abonapp.delete_abongroup'):
                raise PermissionDenied
            get_object_or_404(models.AbonGroup, id=uid).delete()
            messages.success(request, _('delete group success msg'))
            return mydefs.res_success(request, 'abonapp:group_list')
        else:
            messages.warning(request, _('I not know what to delete'))
    except NasNetworkError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, _("NAS says: '%s'") % e)
    return redirect('abonapp:group_list')


@login_required
@permission_required('abonapp.can_add_ballance')
def abonamount(request, gid, uid):
    abon = get_object_or_404(models.Abon, id=uid)
    try:
        if request.method == 'POST':
            abonid = mydefs.safe_int(request.POST.get('abonid'))
            if abonid == int(uid):
                amnt = mydefs.safe_float(request.POST.get('amount'))
                abon.add_ballance(request.user, amnt, comment=_('fill account through admin side'))
                abon.save(update_fields=['ballance'])
                messages.success(request, _('Account filled successfully on %.2f') % amnt)
                return redirect('abonapp:abon_home', gid=gid, uid=uid)
            else:
                messages.error(request, _('I not know the account id'))
    except NasNetworkError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    return render_to_text('abonapp/modal_abonamount.html', {
        'abon': abon,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid)
    }, request=request)


@login_required
@mydefs.only_admins
def invoice_for_payment(request, gid, uid):
    abon = get_object_or_404(models.Abon, id=uid)
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
    abon = get_object_or_404(models.Abon, id=uid)
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
    abon = get_object_or_404(models.Abon, id=uid)
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
    abon = get_object_or_404(models.Abon, id=uid)
    abon_group = get_object_or_404(models.AbonGroup, id=gid)
    frm, passw = None, None
    try:
        if request.method == 'POST':
            if not request.user.has_perm('abonapp.change_abon'):
                raise PermissionDenied
            frm = forms.AbonForm(request.POST, instance=abon)
            if frm.is_valid():
                ip_str = request.POST.get('ip')
                if ip_str:
                    ip = IpPoolItem.objects.get(ip=ip_str)
                    abon.ip_address = ip
                else:
                    abon.ip_address = None
                frm.save()
                messages.success(request, _('edit abon success msg'))
            else:
                messages.warning(request, _('fix form errors'))
        else:
            passw = models.AbonRawPassword.objects.get(account=abon).passw_text
            frm = forms.AbonForm(instance=abon, initial={'password': passw})
    except IntegrityError as e:
        messages.error(request, _('Ip address already exist. %s') % e)
        frm = forms.AbonForm(instance=abon, initial={'password': passw})

    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
    except IpPoolItem.DoesNotExist:
        messages.error(request, _('Ip address not found'))
    except models.AbonRawPassword.DoesNotExist:
        messages.warning(request, _('User has not have password, and cannot login'))

    if request.user.has_perm('abonapp.change_abon'):
        return render(request, 'abonapp/editAbon.html', {
            'form': frm or forms.AbonForm(instance=abon, initial={'password': passw}),
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address
        })
    else:
        return render(request, 'abonapp/viewAbon.html', {
            'abon': abon,
            'abon_group': abon_group,
            'ip': abon.ip_address,
            'passw': passw
        })


@mydefs.require_ssl
def terminal_pay(request):
    from .pay_systems import allpay
    ret_text = allpay(request)
    return HttpResponse(ret_text)


@login_required
@permission_required('abonapp.add_invoiceforpayment')
def add_invoice(request, gid, uid):
    uid = mydefs.safe_int(uid)
    abon = get_object_or_404(models.Abon, id=uid)
    grp = get_object_or_404(models.AbonGroup, id=gid)

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

    except NasNetworkError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    return render(request, 'abonapp/addInvoice.html', {
        'abon': abon,
        'invcount': models.InvoiceForPayment.objects.filter(abon=abon).count(),
        'abon_group': grp
    })


@login_required
@permission_required('abonapp.can_buy_tariff')
def pick_tariff(request, gid, uid):
    grp = get_object_or_404(models.AbonGroup, id=gid)
    abon = get_object_or_404(models.Abon, id=uid)
    tariffs = grp.tariffs.all()
    try:
        if request.method == 'POST':
            trf = Tariff.objects.get(pk=request.POST.get('tariff'))
            abon.pick_tariff(trf, request.user)
            messages.success(request, _('Tariff has been picked'))
            return redirect('abonapp:abon_services', gid=gid, uid=abon.id)
    except models.LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)
        return redirect('abonapp:abon_services', gid=gid, uid=abon.id)
    except Tariff.DoesNotExist:
        messages.error(request, _('Tariff your picked does not exist'))

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

    current_abon_tariff = get_object_or_404(models.AbonTariff, id=t)

    try:
        if act == 'up':
            current_abon_tariff.priority_up()
        elif act == 'down':
            current_abon_tariff.priority_down()
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.error(request, e)

    return redirect('abonapp:abon_home', gid=gid, uid=uid)


@login_required
@permission_required('abonapp.can_complete_service')
def complete_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, id=srvid)
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

    except models.LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
        return redirect('abonapp:abon_home', gid, uid)

    return render(request, 'abonapp/complete_service.html', {
        'abtar': abtar,
        'abon': abon,
        'time_use': time_use,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'tcost': round(res_amount, 4),
        'cashback': round(cashback, 4)
    })


@login_required
@permission_required('abonapp.can_activate_service')
def activate_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, id=srvid)
    amount = abtar.calc_amount_service()

    try:
        if request.method == 'POST':
            if request.POST.get('finish_confirm') != 'yes':
                return HttpResponse(_('Not confirmed'))

            abtar.activate(request.user)
            messages.success(request, _('Service has been activated successfully'))
            return redirect('abonapp:abon_services', gid, uid)

    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except models.LogicError as e:
        messages.error(request, e)
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
        get_object_or_404(models.AbonTariff, id=int(srvid)).delete()
        messages.success(request, _('User has been detached from service'))
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
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
    return redirect('abonapp:people_list', gid=group_id)


@login_required
@mydefs.only_admins
def task_log(request, gid, uid):
    from taskapp.models import Task
    abon = get_object_or_404(models.Abon, id=uid)
    tasks = Task.objects.filter(abon=abon)
    return render(request, 'abonapp/task_log.html', {
        'tasks': tasks,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'abon': abon
    })


@login_required
@mydefs.only_admins
def passport_view(request, gid, uid):
    abon = get_object_or_404(models.Abon, id=uid)
    return render(request, 'abonapp/passport_view.html', {
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'abon': abon
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


# API's

def abons(request):
    ablist = [{
        'id': abn.id,
        'tarif_id': abn.active_tariff().id if abn.active_tariff() else 0,
        'ip': abn.ip_address.int_ip(),
        'is_active': abn.is_active
    } for abn in models.Abon.objects.all()]

    tarlist = [{
        'id': trf.id,
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
    results = [{'id':usr.id, 'name':usr.username, 'fio':usr.fio} for usr in results]
    return HttpResponse(dumps(results, ensure_ascii=False))
