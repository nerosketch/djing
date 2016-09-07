# -*- coding: utf-8 -*-
from json import dumps
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts_app.models import UserProfile
from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff
from django.template.context_processors import csrf
from django.http import HttpResponse, Http404
from agent import get_TransmitterClientKlass, NetExcept
import forms
import models
import mydefs


@login_required
def peoples(request, gid):

    peopleslist = models.Abon.objects.filter(group=gid)

    # фильтр
    dir, field = mydefs.order_helper(request)
    if field:
        peopleslist = peopleslist.order_by(field)


    peopleslist = mydefs.pag_mn(request, peopleslist)

    return render(request, 'abonapp/peoples.html', {
        'peoples': peopleslist,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'dir': dir,
        'order_by': request.GET.get('order_by')
    })


@login_required
# @permission_required('abonapp.add_abongroup')
def addgroup(request):
    warntext = ''
    frm = forms.AbonGroupForm()
    if request.method == 'POST':
        frm = forms.AbonGroupForm(request.POST)
        if frm.is_valid():
            frm.save()
            return redirect('abongroup_list_link')
        else:
            warntext = u'Исправьте ошибки'
    return render(request, 'abonapp/addGroup.html', {
        'csrf_token': csrf(request)['csrf_token'],
        'form': frm,
        'warntext': warntext
    })


@login_required
def grouplist(request):
    groups = models.AbonGroup.objects.annotate(usercount=Count('abon'))

    # фильтр
    dir, field = mydefs.order_helper(request)
    if field:
        groups = groups.order_by(field)

    groups = mydefs.pag_mn(request, groups)

    return render(request, 'abonapp/group_list.html', {
        'groups': groups,
        'dir': dir,
        'order_by': request.GET.get('order_by')
    })


@login_required
def delgroup(request):
    agd = mydefs.safe_int(request.GET.get('id'))
    get_object_or_404(models.AbonGroup, id=agd).delete()
    return mydefs.res_success(request, 'abongroup_list_link')


@login_required
# @permission_required('abonapp.add_abon')
# @permission_required('abonapp.change_abon')
def addabon(request, gid):
    warntext = ''
    frm = None
    try:
        grp = get_object_or_404(models.AbonGroup, id=gid)
        if request.method == 'POST':
            frm = forms.AbonForm(request.POST)
            if frm.is_valid():
                prf = models.Abon()
                prf.group = grp
                prf.save_form(frm)
                prf.save()
                return redirect('people_list_link', grp.id)
            else:
                warntext = u'Некоторые поля заполнены не правильно, проверте ещё раз'

    except IntegrityError, e:
        warntext = "%s: %s" % (warntext, e)

    except models.LogicError as e:
        warntext = e.value

    if not frm:
        frm = forms.AbonForm(initial={
            'ip_address': IpPoolItem.objects.get_free_ip(),
            'group': grp
        })

    return render(request, 'abonapp/addAbon.html', {
        'warntext': warntext,
        'csrf_token': csrf(request)['csrf_token'],
        'form': frm,
        'abon_group': grp
    })


@login_required
# @permission_required('abonapp.delete_abon')
# @permission_required('abonapp.delete_abongroup')
def delentity(request):
    typ = request.GET.get('t')
    uid = request.GET.get('id')

    if typ == 'a':
        abon = get_object_or_404(models.Abon, id=uid)
        gid = abon.group.id
        abon.delete()
        return mydefs.res_success(request, resolve_url('people_list_link', gid))
    elif typ == 'g':
        get_object_or_404(models.AbonGroup, id=uid).delete()
    return mydefs.res_success(request, 'abongroup_list_link')


@login_required
def abonamount(request, gid, uid):
    warntext=''
    abon = get_object_or_404(models.Abon, id=uid)
    if request.method == 'POST':
        abonid = mydefs.safe_int(request.POST.get('abonid'))
        if abonid == int(uid):
            amnt = mydefs.safe_float(request.POST.get('amount'))
            abon.add_ballance(request.user, amnt)
            abon.save()
            return redirect('abonhome_link', gid=gid, uid=uid)
        else:
            warntext = u'Не правильно выбран абонент как цель для пополнения'
    return render(request, 'abonapp/abonamount.html', {
        'abon': abon,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'warntext': warntext
    })


@login_required
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
def abon_services(request, gid, uid):
    abon = get_object_or_404(models.Abon, id=uid)
    abon_tarifs = models.AbonTariff.objects.filter(abon=abon).order_by('tariff_priority')

    return render(request, 'abonapp/services.html', {
        'abon': abon,
        'abon_tarifs': abon_tarifs,
        'active_abontariff_id': abon_tarifs[0].id if abon_tarifs.count() > 0 else None,
        'abon_group': abon.group
    })


@login_required
def abonhome(request, gid, uid):
    abon = get_object_or_404(models.Abon, id=uid)
    abon_group = get_object_or_404(models.AbonGroup, id=gid)
    warntext = ''
    ballance = abon.ballance
    frm = None
    init_frm_dat = {
        'username': abon.username,
        'fio': abon.fio,
        'ip_address': abon.ip_address or u'Не назначен',
        'telephone': abon.telephone,
        'group': abon.group,
        'address': abon.address,
        'is_active': abon.is_active
    }

    try:
        if request.method == 'POST':
            # подключение к NAS'у в начале для того чтоб если исключение то ничего не сохранялось и сразу показать ошибку
            tc = get_TransmitterClientKlass()()
            frm = forms.AbonForm(request.POST)
            if frm.is_valid():
                cd = frm.cleaned_data
                abon.username = cd['username']
                abon.fio = cd['fio']

                ip_address = abon.ip_address
                abon.ip_address = get_object_or_404(IpPoolItem, ip=cd['ip_address'])

                abon.telephone = cd['telephone']
                abon.group = cd['group']
                abon.address = cd['address']
                abisactive = abon.is_active
                abon.is_active = 1 if cd['is_active'] else 0
                abon.save()

                # Если включили абонента то шлём событие от этом
                if cd['is_active'] and not abisactive:
                    # смотрим есть-ли доступ у абонента к услуге
                    is_acc = abon.is_access()
                    if is_acc:
                        tc.signal_abon_refresh_info(abon)
                    else:
                        tc.signal_abon_close_inet(abon)


                # Если выключили абонента
                elif not cd['is_active'] and abisactive:
                    tc.signal_abon_disable(abon)

                # Если изменили инфу, важную для NAS то говорим NAS'у перечитать инфу об абоненте
                if abon.ip_address != ip_address:
                    tc.signal_abon_refresh_info(abon)

                #return redirect('abonhome_link', gid, uid)
            else:
                warntext = u'Не правильные значения, проверте поля и попробуйте ещё'
        else:
            frm = forms.AbonForm(initial=init_frm_dat)
    except IntegrityError, e:
        warntext = u'Проверте введённые вами значения, скорее всего такой ip уже у кого-то есть. А вообще: %s' % e
        frm = forms.AbonForm(initial=init_frm_dat)

    except Http404:
        warntext = u'Ip адрес не найден в списке IP адресов'
        frm = forms.AbonForm(initial=init_frm_dat)

    except NetExcept as e:
        warntext = e.value

    return render(request, 'abonapp/editAbon.html', {
        'warntext': warntext,
        'form': frm or forms.AbonForm(initial=init_frm_dat),
        'abon': abon,
        'ballance': ballance,
        'abon_group': abon_group
    })


def terminal_pay(request):
    username = request.GET.get('username')
    amount = mydefs.safe_float(request.GET.get('amount'))

    kernel_user = get_object_or_404(UserProfile, username='kernel')
    abon = get_object_or_404(models.Abon, username=username)

    abon.add_ballance(kernel_user, amount)

    abon.save()
    return HttpResponse('ok')


@login_required
# @permission_required('abonapp.add_invoiceforpayment')
def add_invoice(request, gid, uid):
    uid = mydefs.safe_int(uid)
    abon = get_object_or_404(models.Abon, id=uid)
    grp = get_object_or_404(models.AbonGroup, id=gid)

    if request.method == 'POST':
        curr_amount = mydefs.safe_int(request.POST.get('curr_amount'))
        comment = request.POST.get('comment')

        newinv = models.InvoiceForPayment()
        newinv.abon = abon
        newinv.amount = curr_amount
        newinv.comment = comment

        if request.POST.get('status') == u'on':
            newinv.status = True

        newinv.author = request.user
        newinv.save()
        return redirect('abonhome_link', gid=gid, uid=uid)
    else:
        return render(request, 'abonapp/addInvoice.html', {
            'csrf_token': csrf(request)['csrf_token'],
            'abon': abon,
            'invcount': models.InvoiceForPayment.objects.filter(abon=abon).count(),
            'abon_group': grp
        })


@login_required
def buy_tariff(request, gid, uid):
    warntext = ''
    frm = None
    grp = get_object_or_404(models.AbonGroup, id=gid)
    abon = get_object_or_404(models.Abon, id=uid)
    try:
        if request.method == 'POST':
            frm = forms.BuyTariff(request.POST)
            if frm.is_valid():
                cd = frm.cleaned_data
                abon.buy_tariff(cd['tariff'], request.user)
                abon.save()
                return redirect('abonhome_link', gid=gid, uid=abon.id)
            else:
                warntext = u'Что-то не так при покупке услуги, проверьте и попробуйте ещё'
        else:
            frm = forms.BuyTariff()
    except models.LogicError as e:
        warntext = e.value

    except NetExcept as e:
        warntext = e.value

    return render(request, 'abonapp/buy_tariff.html', {
        'warntext': warntext,
        'form': frm or forms.BuyTariff(),
        'abon': abon,
        'abon_group': grp
    })


@login_required
def chpriority(request, gid, uid):
    t = request.GET.get('t')
    act = request.GET.get('a')

    current_abon_tariff = get_object_or_404(models.AbonTariff, id=t)

    if act == 'up':
        current_abon_tariff.priority_up()
    elif act == 'down':
        current_abon_tariff.priority_down()

    return redirect('abonhome_link', gid=gid, uid=uid)


@login_required
def complete_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, id=srvid)
    abon_group = get_object_or_404(models.AbonGroup, id=gid)

    if abtar.abon.id != int(uid):
        return HttpResponse('<h1>uid not equal uid from service</h1>')

    try:
        if request.method == 'POST':
            tc = get_TransmitterClientKlass()()
            abon = abtar.abon
            # досрочно завершаем услугу
            try:
                # пробуем активировать следующую услугу
                abtar.finish_and_activate_next_tariff(request.user)

            except models.LogicError:
                # Значит у абонента нет следующих услуг. Игнорим, далее в tariff.manage_access() всё разрулится
                pass

            # завершаем текущую услугу.
            abtar.delete()

            # Переупорядочиваем приоритеты
            models.AbonTariff.objects.update_priorities(abon)

            # проверяем, может-ли абонент пользоваться новым тарифным планом
            if abon.is_access():
                # обновляем инфу об абоненте, чтоб применился новый тариф
                tc.signal_abon_refresh_info(abon)
            else:
                # если доступа нет - закрываем инет
                tc.signal_abon_close_inet(abon)

            return redirect('abonhome_link', gid, uid)

        next_tariff = models.AbonTariff.objects.filter(
            abon=abtar.abon,
            tariff_priority__gt=abtar.tariff_priority
        )[:1]

        if not abtar.time_start:
            abtar.time_start = timezone.now()
            abtar.save()

        time_use = timezone.now() - abtar.time_start
        time_use = {
            'days': time_use.days,
            'hours': time_use.seconds / 3600,
            'minutes': time_use.seconds / 60 % 60
        }
        return render(request, 'abonapp/complete_service.html', {
            'abtar': abtar,
            'abon': abtar.abon,
            'next_tariff': next_tariff[0] if next_tariff.count() > 0 else None,
            'time_use': time_use,
            'abon_group': abon_group
        })

    except models.LogicError as e:
        warntext = e.value

    except NetExcept as e:
        warntext = e.value

    return render(request, 'abonapp/complete_service.html', {
        'abtar': abtar,
        'abon': abtar.abon,
        'warntext': warntext,
        'abon_group': abon_group
    })


@login_required
def log_page(request):
    logs = models.AbonLog.objects.all()

    logs = mydefs.pag_mn(request, logs)

    return render(request, 'abonapp/log.html', {
        'logs': logs
    })


# API's

def abons(request):
    ablist = map(lambda abn: {
        'id': abn.id,
        'tarif_id': abn.active_tariff().id if abn.active_tariff() else 0,
        'ip': abn.ip_address.int_ip(),
        'is_active': abn.is_active
    }, models.Abon.objects.all())

    tarlist = map(lambda trf: {
        'id': trf.id,
        'speedIn': trf.speedIn,
        'speedOut': trf.speedOut
    }, Tariff.objects.all())

    data = {
        'subscribers': ablist,
        'tariffs': tarlist
    }
    del ablist, tarlist
    return HttpResponse(dumps(data))
