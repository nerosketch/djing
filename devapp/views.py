# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from easysnmp import EasySNMPTimeoutError, EasySNMPError

from .models import Device
from mydefs import pag_mn, res_success, res_error, only_admins, ping, order_helper
from .forms import DeviceForm
from abonapp.models import AbonGroup


@login_required
@only_admins
def devices(request, grp):
    group = get_object_or_404(AbonGroup, pk=grp)
    devs = Device.objects.filter(user_group=grp)

    # фильтр
    dr, field = order_helper(request)
    if field:
        devs = devs.order_by(field)

    devs = pag_mn(request, devs)

    return render(request, 'devapp/devices.html', {
        'devices': devs,
        'dir': dr,
        'order_by': request.GET.get('order_by'),
        'group': group
    })


@login_required
@only_admins
def devices_null_group(request):
    devs = Device.objects.filter(user_group=None)
    # фильтр
    dr, field = order_helper(request)
    if field:
        devs = devs.order_by(field)

    devs = pag_mn(request, devs)

    return render(request, 'devapp/devices_null_group.html', {
        'devices': devs,
        'dir': dr,
        'order_by': request.GET.get('order_by')
    })


@login_required
@permission_required('devapp.delete_device')
def devdel(request, did):
    try:
        dev = Device.objects.get(pk=did)
        back_url = resolve_url('devapp:devs', grp=dev.user_group.pk if dev.user_group else 0)
        dev.delete()
        return res_success(request, back_url)
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

    if devinst is None:
        return render(request, 'devapp/add_dev.html', {
            'form': frm
        })
    else:
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
    template_name = 'devapp/ports.html'
    try:
        if ping(dev.ip_address):
            if dev.man_passw:
                manager = dev.get_manager_klass()(dev.ip_address, dev.man_passw)
                uptime = manager.uptime()
                ports = manager.get_ports()
                template_name = manager.get_template_name()
            else:
                messages.warning(request, _('Not Set snmp device password'))
        else:
            messages.error(request, _('Dot was not pinged'))
    except EasySNMPTimeoutError:
        messages.error(request, _('wait for a reply from the SNMP Timeout'))
    except EasySNMPError:
        messages.error(request, _('SNMP error on device'))

    return render(request, template_name, {
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
    return redirect('devapp:view', dev.user_group.pk if dev.user_group is not None else 0, did)


@login_required
@only_admins
def group_list(request):
    groups = AbonGroup.objects.all()
    return render(request, 'devapp/group_list.html', {
        'groups': groups
    })
