from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    return render(request, 'clientsideapp/index.html')


@login_required
def pays(request):
    return render(request, 'clientsideapp/pays.html')


@login_required
def buy_service(request):
    return render(request, 'clientsideapp/buy.html')
