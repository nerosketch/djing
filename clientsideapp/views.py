# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from abonapp.models import AbonLog, AbonTariff, InvoiceForPayment, Abon, LogicError
from tariff_app.models import Tariff
from mydefs import pag_mn


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
def buy_service(request):
    all_tarifs = Tariff.objects.all()

    own_abon_tariffs = AbonTariff.objects.filter(abon_id=request.user.id)

    current_service = own_abon_tariffs.exclude(time_start=None)
    current_service = current_service[0] if current_service.count() > 0 else None

    return render(request, 'clientsideapp/buy.html', {
        'tarifs': all_tarifs,
        'own_abon_tariffs': own_abon_tariffs,
        'current_service': current_service
    })


@login_required
def debts_list(request):
    debts = InvoiceForPayment.objects.filter(abon=request.user)
    return render(request, 'clientsideapp/debts.html', {
        'debts': debts
    })


@login_required
def debt_buy(request, d_id):
    warntext = u''
    debt = get_object_or_404(InvoiceForPayment, id=d_id)
    abon = get_object_or_404(Abon, id=request.user.id)
    if request.method == 'POST':
        try:
            sure = request.POST.get('sure')
            if sure != 'on':
                raise LogicError(u'Вы не уверены что хотите оплатить долг?')
            if abon.ballance < debt.amount:
                raise LogicError(u'Не достаточно средств на счету')

            abon.make_pay(request.user, debt.amount, debt.comment)
            debt.set_ok()
            abon.save(update_fields=['ballance'])
            debt.save(update_fields=['status', 'date_pay'])
            return redirect('client_debts')
        except LogicError, e:
            warntext = e.value
    return render(request, 'clientsideapp/debt_buy.html', {
        'warntext': warntext,
        'debt': debt,
        'amount': debt.amount,
        'ballance_after': abon.ballance - debt.amount
    })
