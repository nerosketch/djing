# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from abonapp.models import AbonLog, InvoiceForPayment, Abon
from tariff_app.models import Tariff
from mydefs import pag_mn, LogicError
from agent import NasFailedResult, NasNetworkError


@login_required
def home(request):
    return render(request, 'clientsideapp/index.html')


@login_required
def pays(request):
    pay_history = AbonLog.objects.filter(abon=request.user).order_by('-id')
    pay_history = pag_mn(request, pay_history)
    return render(request, 'clientsideapp/pays.html', {
        'pay_history': pay_history
    })


@login_required
def services(request):
    try:
        abon = Abon.objects.get(pk=request.user.pk)
        all_tarifs = abon.group.tariffs.filter(is_admin=False)
        current_service = abon.active_tariff()
    except:
        all_tarifs = None
        current_service = None
    return render(request, 'clientsideapp/services.html', {
        'tarifs': all_tarifs,
        'current_service': current_service
    })


@login_required
@transaction.atomic
def buy_service(request, srv_id):
    abon = get_object_or_404(Abon, pk=request.user.pk)
    service = get_object_or_404(Tariff, pk=srv_id)
    try:
        current_service = abon.active_tariff()
        if request.method == 'POST':
            abon.pick_tariff(service, request.user, _("Buy the service via user side, service '%s'")
                             % service)
            messages.success(request, _("The service '%s' wan successfully activated") % service.title)
        else:
            return render_to_text('clientsideapp/modal_service_buy.html', {
                'service': service,
                'current_service': current_service.tariff if current_service is not None else None
            }, request=request)
    except LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    return redirect('client_side:services')


@login_required
def debts_list(request):
    debts = InvoiceForPayment.objects.filter(abon=request.user)
    return render(request, 'clientsideapp/debts.html', {
        'debts': debts
    })


@login_required
@transaction.atomic
def debt_buy(request, d_id):
    debt = get_object_or_404(InvoiceForPayment, id=d_id)
    abon = get_object_or_404(Abon, id=request.user.id)
    if request.method == 'POST':
        try:
            sure = request.POST.get('sure')
            if sure != 'on':
                raise LogicError(_("Are you not sure that you want buy the service?"))
            if abon.ballance < debt.amount:
                raise LogicError(_('Your account have not enough money'))

            abon.make_pay(request.user, debt.amount)
            debt.set_ok()
            abon.save(update_fields=['ballance'])
            debt.save(update_fields=['status', 'date_pay'])
            return redirect('client_side:debts')
        except LogicError as e:
            messages.error(request, e)
        except NasFailedResult as e:
            messages.error(request, e)
        except NasNetworkError as e:
            messages.error(request, e)
    return render(request, 'clientsideapp/debt_buy.html', {
        'debt': debt,
        'amount': debt.amount,
        'ballance_after': abon.ballance - debt.amount
    })
