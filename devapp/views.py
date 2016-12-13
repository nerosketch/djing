# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from models import Device
from mydefs import pag_mn, res_success, res_error, only_admins
from forms import DeviceForm


@login_required
@only_admins
def devices(request):
    devs = Device.objects.all()
    devs = pag_mn(request, devs)

    return render(request, 'devapp/devices.html', {
        'devices': devs
    })


@login_required
@only_admins
def devdel(request, did):
    try:
        get_object_or_404(Device, id=did).delete()
        return res_success(request, 'devapp:devs')
    except:
        return res_error(request, u'Неизвестная ошибка при удалении :(')


@login_required
@only_admins
def dev(request, devid=0):
    warntext = ''
    devinst = get_object_or_404(Device, id=devid) if devid != 0 else None

    if request.method == 'POST':
        frm = DeviceForm(request.POST, instance=devinst)
        if frm.is_valid():
            frm.save()
            return redirect('devapp:devs')
        else:
            warntext = u'Ошибка в данных, проверте их ещё раз'
    else:
        frm = DeviceForm(instance=devinst)

    return render(request, 'devapp/dev.html', {
        'warntext': warntext,
        'form': frm,
        'devid': devid
    })


@login_required
@only_admins
def devview(request, did):
    warntext = ''

    dev = get_object_or_404(Device, id=did)

    return render(request, 'devapp/ports.html', {
        'warntext': warntext,
        'dev': dev
    })
