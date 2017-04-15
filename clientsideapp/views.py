# coding=utf-8
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from abonapp.models import AbonLog, AbonTariff, InvoiceForPayment, Abon, LogicError
from tariff_app.models import Tariff
from mydefs import pag_mn, RuTimedelta
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
    abon = Abon.objects.get(pk=request.user.pk)
    all_tarifs = abon.group.tariffs.filter(is_admin=False)
    own_abon_tariffs = AbonTariff.objects.filter(abon=abon)
    current_service = own_abon_tariffs.exclude(time_start=None)
    current_service = current_service[0] if current_service.count() > 0 else None

    return render(request, 'clientsideapp/services.html', {
        'tarifs': all_tarifs,
        'own_abon_tariffs': own_abon_tariffs,
        'current_service': current_service
    })


@login_required
def buy_service(request, srv_id):
    abon = get_object_or_404(Abon, pk=request.user.pk)
    service = get_object_or_404(Tariff, pk=srv_id)
    try:
        current_service = abon.active_tariff()
        if request.method == 'POST':
            abon.pick_tariff(service, request.user, 'Покупка тарифного плана через личный кабинет, тариф "%s"'
                                       % service)
            messages.success(request, 'Вы подписались на новую услугу. Она встала на очередь подключений. '
                                      'Когда закончится ваша текущая услуга, то включится эта')
        else:
            return render_to_text('clientsideapp/modal_service_buy.html', {
                'service': service,
                'current_service': current_service
            }, request=request)
    except LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    return redirect('client_side:services')


@login_required
def complete_service(request, srv_id):
    abtar = get_object_or_404(AbonTariff, id=srv_id)
    service = abtar.tariff

    try:
        if request.method == 'POST':
            # досрочно завершаем услугу
            finish_confirm = request.POST.get('finish_confirm')
            if finish_confirm == 'yes':
                # удаляем запись о текущей услуге.
                abtar.delete()
                messages.success(request, 'Услуга "%s" успешно завершена' % service.title)
                AbonLog.objects.create(
                    abon=abtar.abon,
                    amount=0.0,
                    author=abtar.abon,
                    comment='Досрочное завершение услуги "%s" из личного кабинета' % service.title
                )
            else:
                messages.error(request, 'Действие не подтверждено')
        else:
            time_use = RuTimedelta(timezone.now() - abtar.time_start)
            return render_to_text('clientsideapp/modal_complete_service.html', {
                'service': service,
                'abtar': abtar,
                'time_use': time_use
            }, request=request)
    except LogicError as e:
        messages.error(request, e)
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError:
        messages.error(request, 'Временные неполадки')
    return redirect('client_side:services')


@login_required
def unsubscribe_service(request, srv_id):
    abtar = get_object_or_404(AbonTariff, id=srv_id)
    service = abtar.tariff
    try:
        if request.method == 'POST':
            # досрочно завершаем услугу
            if request.POST.get('finish_confirm') == 'yes':
                AbonTariff.objects.get(pk=srv_id).delete()
                messages.success(request, 'Вы успешно отписались от услуги, "%s"' % service.title)
            else:
                messages.error(request, 'Действие не подтверждено')
        else:
            return render_to_text('clientsideapp/modal_unsubscribe_service.html', {
                'abtar': abtar,
                'service': service
            }, request=request)
    except AbonTariff.DoesNotExist:
        messages.error(request, 'Указанная подписка на услугу не найдена')
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError:
        messages.error(request, 'Временные неполадки')
    return redirect('client_side:services')


@login_required
def activate_service(request, srv_id):
    abtar = get_object_or_404(AbonTariff, id=srv_id)
    service = abtar.tariff
    amount = abtar.calc_amount_service()
    try:
        if request.method == 'POST':
            # активируем услугу
            if request.POST.get('finish_confirm') == 'yes':
                abtar.activate(request.user)
                messages.success(request, 'Услуга "%s" успешно активирована' % service.title)
            else:
                messages.error(request, 'Запрос не подтверждён')
            return redirect('client_side:services')
    except NasFailedResult as e:
        messages.error(request, e)
    except NasNetworkError as e:
        messages.warning(request, e)
    except LogicError as e:
        messages.error(request, e)
    return render_to_text('clientsideapp/modal_activate_service.html', {
        'abtar': abtar,
        'service': service,
        'amount': amount,
        'abon': abtar.abon,
        'diff': abtar.abon.ballance - amount
    }, request=request)


@login_required
def debts_list(request):
    debts = InvoiceForPayment.objects.filter(abon=request.user)
    return render(request, 'clientsideapp/debts.html', {
        'debts': debts
    })


@login_required
def debt_buy(request, d_id):
    debt = get_object_or_404(InvoiceForPayment, id=d_id)
    abon = get_object_or_404(Abon, id=request.user.id)
    if request.method == 'POST':
        try:
            sure = request.POST.get('sure')
            if sure != 'on':
                raise LogicError('Вы не уверены что хотите оплатить долг?')
            if abon.ballance < debt.amount:
                raise LogicError('Не достаточно средств на счету')

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
