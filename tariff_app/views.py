# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from .models import Tariff
import mydefs
from . import forms


@login_required
@mydefs.only_admins
def tarifs(request):
    tars = Tariff.objects.all()

    # фильтр
    direct, field = mydefs.order_helper(request)
    if field:
        tars = tars.order_by(field)

    tars = mydefs.pag_mn(request, tars)

    return render(request, 'tariff_app/tarifs.html', {
        'tariflist': tars,
        'dir': direct,
        'order_by': request.GET.get('order_by')
    })


@login_required
def edit_tarif(request, tarif_id=0):
    tarif_id = mydefs.safe_int(tarif_id)

    if tarif_id == 0:
        if not request.user.has_perm('tariff_app.add_tariff'):
            raise PermissionDenied
    else:
        if not request.user.has_perm('tariff_app.change_tariff'):
            raise PermissionDenied

    if request.method == 'POST':
        frm = forms.TariffForm(request.POST)
        if frm.is_valid():
            frm.save()
            return redirect('tarifs:home')
        else:
            messages.warning(request, 'Не все поля заполнены правильно, проверте и попробуйте ещё раз')
    else:
        if tarif_id == 0:
            tarif = Tariff()
        else:
            tarif = get_object_or_404(Tariff, id=tarif_id)
        frm = forms.TariffForm(instance=tarif)

    return render(request, 'tariff_app/editTarif.html', {
        'form': frm,
        'tarif_id': tarif_id
    })


@login_required
@permission_required('tariff_app.delete_tariff')
def del_tarif(request, id):
    tar_id = mydefs.safe_int(id)
    get_object_or_404(Tariff, id=tar_id).delete()
    return mydefs.res_success(request, 'tarifs:home')
