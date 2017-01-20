# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Device
from mydefs import pag_mn, res_success, res_error, only_admins, ping
from .forms import DeviceForm


@login_required
@only_admins
def devices(request):
    devs = Device.objects.all()
    devs = pag_mn(request, devs)

    return render(request, 'devapp/devices.html', {
        'devices': devs
    })


@login_required
@permission_required('devapp.delete_device')
def devdel(request, did):
    try:
        get_object_or_404(Device, id=did).delete()
        return res_success(request, 'devapp:devs')
    except:
        return res_error(request, 'Неизвестная ошибка при удалении :(')


@login_required
@only_admins
def dev(request, devid=0):
    devinst = get_object_or_404(Device, id=devid) if devid != 0 else None

    if request.method == 'POST':
        if devid == 0:
            if not request.user.has_perm('devapp.add_device'):
                raise PermissionDenied
        else:
            if not request.user.has_perm('devapp.change_device'):
                raise PermissionDenied
        frm = DeviceForm(request.POST, instance=devinst)
        if frm.is_valid():
            frm.save()
            return redirect('devapp:view', did=devid)
        else:
            messages.error(request, 'Ошибка в данных, проверте их ещё раз')
    else:
        frm = DeviceForm(instance=devinst)

    return render(request, 'devapp/dev.html', {
        'form': frm,
        'dev': devinst
    })


@login_required
@only_admins
def devview(request, did):

    ports = None
    uptime = 0
    dev = get_object_or_404(Device, id=did)
    if ping(dev.ip_address):
        if dev.man_passw:
            manager = dev.get_manager_klass()(dev.ip_address, dev.man_passw)
            uptime = manager.uptime()
            ports = manager.get_ports()
        else:
            messages.warning(request, 'Не указан snmp пароль для устройства')
    else:
        messages.error(request, 'Эта точка не пингуется')

    return render(request, 'devapp/ports.html', {
        'dev': dev,
        'ports': ports,
        'uptime': uptime
    })


@login_required
@only_admins
def toggle_port(request, did, portid, status=0):
    portid = int(portid)
    status = int(status)
    dev = get_object_or_404(Device, id=int(did))
    if ping(dev.ip_address):
        if dev.man_passw:
            manager = dev.get_manager_klass()(dev.ip_address, dev.man_passw)
            ports = manager.get_ports()
            if status:
                ports[portid-1].enable()
            else:
                ports[portid-1].disable()
        else:
            messages.warning(request, 'Не указан snmp пароль для устройства')
    else:
        messages.error(request, 'Эта точка не пингуется')
    return redirect('devapp:view', did=did)
