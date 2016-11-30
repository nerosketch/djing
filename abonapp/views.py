# -*- coding: utf-8 -*-
from json import dumps

from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.context_processors import csrf
from django.http import HttpResponse, Http404
from django.contrib.auth import get_user_model

from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff
from agent import NetExcept
import forms
import models
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
@mydefs.only_admins
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
@mydefs.only_admins
def delgroup(request):
    agd = mydefs.safe_int(request.GET.get('id'))
    get_object_or_404(models.AbonGroup, id=agd).delete()
    return mydefs.res_success(request, 'abongroup_list_link')


@login_required
@mydefs.only_admins
# @permission_required('abonapp.add_abon')
# @permission_required('abonapp.change_abon')
def addabon(request, gid):
    warning_text = ''
    frm = None
    group = None
    try:
        group = get_object_or_404(models.AbonGroup, id=gid)
        if request.method == 'POST':
            frm = forms.AbonForm(request.POST)
            if frm.is_valid():
                prf = models.Abon()
                prf.group = group
                prf.save_form(frm)
                prf.save()
                return redirect('people_list_link', group.id)
            else:
                warning_text = u'Некоторые поля заполнены не правильно, проверте ещё раз'

    except IntegrityError, e:
        warning_text = "%s: %s" % (warning_text, e)

    except models.LogicError as e:
        warning_text = e.value

    if not frm:
        frm = forms.AbonForm(initial={
            'ip_address': IpPoolItem.objects.get_free_ip(),
            'group': group
        })

    return render(request, 'abonapp/addAbon.html', {
        'warntext': warning_text,
        'csrf_token': csrf(request)['csrf_token'],
        'form': frm,
        'abon_group': group
    })


@login_required
@mydefs.only_admins
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
@mydefs.only_admins
def abonamount(request, gid, uid):
    warning_text = ''
    abon = get_object_or_404(models.Abon, id=uid)
    if request.method == 'POST':
        abonid = mydefs.safe_int(request.POST.get('abonid'))
        if abonid == int(uid):
            amnt = mydefs.safe_float(request.POST.get('amount'))
            abon.add_ballance(request.user, amnt)
            abon.save(update_fields=['ballance'])
            return redirect('abonhome_link', gid=gid, uid=uid)
        else:
            warning_text = u'Не правильно выбран абонент как цель для пополнения'
    return render(request, 'abonapp/abonamount.html', {
        'abon': abon,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid),
        'warntext': warning_text
    })


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
            frm = forms.AbonForm(request.POST)
            if frm.is_valid():
                cd = frm.cleaned_data
                abon.username = cd['username']
                abon.fio = cd['fio']
                abon.ip_address = get_object_or_404(IpPoolItem, ip=cd['ip_address'])
                abon.telephone = cd['telephone']
                abon.group = cd['group']
                abon.address = cd['address']
                abon.is_active = 1 if cd['is_active'] else 0
                abon.save()

                # return redirect('abonhome_link', gid, uid)
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

    kernel_user = get_object_or_404(get_user_model(), username='kernel')
    abon = get_object_or_404(models.Abon, username=username)

    abon.add_ballance(kernel_user, amount)

    abon.save(update_fields=['ballance'])
    return HttpResponse('ok')


@login_required
@mydefs.only_admins
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
@mydefs.only_admins
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
        warntext = e.value + u', но услуга уже подключена, она будет применена когда будет восстановлен доступ к NAS серверу.' \
                             u' <a href="%s">Вернуться</a>' % resolve_url('abonhome_link', gid=gid, uid=abon.id)

    return render(request, 'abonapp/buy_tariff.html', {
        'warntext': warntext,
        'form': frm or forms.BuyTariff(),
        'abon': abon,
        'abon_group': grp
    })


@login_required
@mydefs.only_admins
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
@mydefs.only_admins
def complete_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, id=srvid)

    if abtar.abon.id != int(uid):
        return HttpResponse('<h1>uid not equal uid from service</h1>')

    try:
        if request.method == 'POST':
            # досрочно завершаем услугу
            finish_confirm = request.POST.get('finish_confirm')
            if finish_confirm == 'yes':
                # удаляем запись о текущей услуге.
                abtar.delete()
                return redirect('abonhome_link', gid, uid)
            else:
                raise models.LogicError('Действие не подтверждено')

        time_use = timezone.now() - abtar.time_start
        time_use = {
            'days': time_use.days,
            'hours': time_use.seconds / 3600,
            'minutes': time_use.seconds / 60 % 60
        }
        return render(request, 'abonapp/complete_service.html', {
            'abtar': abtar,
            'abon': abtar.abon,
            'time_use': time_use,
            'abon_group': get_object_or_404(models.AbonGroup, id=gid)
        })

    except models.LogicError as e:
        warntext = e.value

    except NetExcept as e:
        warntext = e.value

    return render(request, 'abonapp/complete_service.html', {
        'abtar': abtar,
        'abon': abtar.abon,
        'warntext': warntext,
        'abon_group': get_object_or_404(models.AbonGroup, id=gid)
    })


@login_required
@mydefs.only_admins
def activate_service(request, gid, uid, srvid):
    abtar = get_object_or_404(models.AbonTariff, id=srvid)

    if request.method == 'POST':
        if request.POST.get('finish_confirm') != 'yes':
            return HttpResponse('<h1>Request not confirmed</h1>')

        abtar.activate(request.user)
        return redirect('abonhome_link', gid, uid)

    amount = abtar.calc_amount_service()
    return render(request, 'abonapp/activate_service.html', {
        'abon': abtar.abon,
        'abon_group': abtar.abon.group,
        'abtar': abtar,
        'amount': amount,
        'diff': abtar.abon.ballance - amount
    })


@login_required
@mydefs.only_admins
def unsubscribe_service(request, gid, uid, srvid):
    get_object_or_404(models.AbonTariff, id=int(srvid)).delete()
    return redirect('abonhome_link', gid=gid, uid=uid)


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
