# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from models import Tariff
import mydefs
import forms


@login_required
@mydefs.only_admins
def tarifs(request):
    tars = Tariff.objects.all()

    # фильтр
    dir, field = mydefs.order_helper(request)
    if field:
        tars = tars.order_by(field)

    tars = mydefs.pag_mn(request, tars)

    return render(request, 'tariff_app/tarifs.html', {
        'tariflist': tars,
        'dir': dir,
        'order_by': request.GET.get('order_by')
    })


@login_required
@mydefs.only_admins
def edit_tarif(request, tarif_id=0):
    tarif_id = mydefs.safe_int(tarif_id)

    warntext = ''
    if request.method == 'POST':
        frm = forms.TariffForm(request.POST)
        if frm.is_valid():
            frm.save()
            return redirect('tarifs_link')
        else:
            warntext = u'Не все поля заполнены правильно, проверте и попробуйте ещё раз'
    else:
        if tarif_id == 0:
            tarif = Tariff()
        else:
            tarif = get_object_or_404(Tariff, id=tarif_id)
        frm = forms.TariffForm(instance=tarif)

    return render(request, 'tariff_app/editTarif.html', {
        'warntext': warntext,
        'form': frm,
        'tarif_id': tarif_id
    })


@login_required
@mydefs.only_admins
def del_tarif(request, id):
    tar_id = mydefs.safe_int(id)
    get_object_or_404(Tariff, id=tar_id).delete()
    return mydefs.res_success(request, 'tarifs_link')
