from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from abonapp.models import AbonLog, AbonTariff
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
