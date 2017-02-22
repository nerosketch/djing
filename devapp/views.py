# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import ugettext as _
from easysnmp import EasySNMPTimeoutError

from .models import Device
from mydefs import pag_mn, res_success, res_error, only_admins, ping, order_helper
from .forms import DeviceForm


@login_required
@only_admins
def devices(request):
    devs = Device.objects.all()

    # фильтр
    dr, field = order_helper(request)
    if field:
        devs = devs.order_by(field)
    print(type(request.GET), request.GET)
    import django.http.request

    devs = pag_mn(request, devs)

    return render(request, 'devapp/devices.html', {
        'devices': devs,
        'dir': dr,
        'order_by': request.GET.get('order_by')
    })


@login_required
@permission_required('devapp.delete_device')
def devdel(request, did):
    try:
        Device.objects.get(pk=did).delete()
        return res_success(request, 'devapp:devs')
    except Device.DoesNotExist:
        return res_error(request, _('Delete failed'))


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
            messages.success(request, _('Device info has been saved'))
        else:
            messages.error(request, _('Form is invalid, check fields and try again'))
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
    try:
        if ping(dev.ip_address):
            if dev.man_passw:
                manager = dev.get_manager_klass()(dev.ip_address, dev.man_passw)
                uptime = manager.uptime()
                ports = manager.get_ports()
            else:
                messages.warning(request, _('Not Set snmp device password'))
        else:
            messages.error(request, _('Dot was not pinged'))
    except EasySNMPTimeoutError:
        messages.error(request, _('wait for a reply from the SNMP Timeout'))

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
            messages.warning(request, _('Not Set snmp device password'))
    else:
        messages.error(request, _('Dot was not pinged'))
    return redirect('devapp:view', did=did)
