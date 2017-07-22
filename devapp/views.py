# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from easysnmp import EasySNMPTimeoutError, EasySNMPError
from json import dumps

from .models import Device, Port, DeviceDBException
from mydefs import pag_mn, res_success, res_error, only_admins, ping, order_helper
from .forms import DeviceForm, PortForm
from abonapp.models import AbonGroup, Abon
from djing.settings import DEFAULT_SNMP_PASSWORD


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
    except DeviceDBException as e:
        return res_error(request, e)


@login_required
@only_admins
def dev(request, grp, devid=0):
    devinst = get_object_or_404(Device, id=devid) if devid != 0 else None
    user_group = get_object_or_404(AbonGroup, pk=grp)

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
            return redirect('devapp:devs', grp)
        else:
            messages.error(request, _('Form is invalid, check fields and try again'))
    else:
        if devinst is None:
            frm = DeviceForm(initial={
                'user_group': user_group,
                'devtype': request.GET.get('t'),
                'mac_addr': request.GET.get('mac'),
                'comment': request.GET.get('c'),
                'ip_address': request.GET.get('ip'),
                'man_passw': DEFAULT_SNMP_PASSWORD
            })
        else:
            frm = DeviceForm(instance=devinst)

    if devinst is None:
        return render(request, 'devapp/add_dev.html', {
            'form': frm,
            'group': user_group
        })
    else:
        return render(request, 'devapp/dev.html', {
            'form': frm,
            'dev': devinst,
            'selected_parent_dev': devinst.parent_dev or None
        })


@login_required
@permission_required('devapp.change_device')
def manage_ports(request, devid):
    try:
        dev = Device.objects.get(pk=devid)
        if dev.user_group is None:
            messages.error(request, _('Device is not have a group, please fix that'))
            return redirect('devapp:group_list')
        ports = Port.objects.filter(device=dev)

    except Device.DoesNotExist:
        messages.error(request, _('Device does not exist'))
        return redirect('devapp:view', dev.user_group.pk if dev.user_group else 0, did=devid)
    except DeviceDBException as e:
        messages.error(request, e)
    return render(request, 'devapp/manage_ports/list.html', {
        'ports': ports,
        'dev': dev
    })


@login_required
@permission_required('devapp.add_port')
def add_ports(request, devid):
    class TempPort:
        def __init__(self, pid, text, status, from_db, pk=None):
            self.pid = pid
            self.text = text
            self.status = status
            self.from_db = from_db
            self.pk = pk

        def __eq__(self, other):
            return self.pid == other.pid

        def __hash__(self):
            return self.pid

        def __str__(self):
            return "p:%d\tM:%s\tT:%s" % (self.pid, self.text)

    try:
        res_ports = list()
        dev = Device.objects.get(pk=devid)
        if dev.user_group is None:
            messages.error(request, _('Device is not have a group, please fix that'))
            return redirect('devapp:group_list')
        if request.method == 'POST':
            ports = zip(
                request.POST.getlist('p_text'),
                request.POST.getlist('pids')
            )
            for port_text, port_num in ports:
                if port_text == '' or port_text is None:
                    continue
                try:
                    port = Port.objects.get(num=port_num, device=dev)
                    port.descr = port_text
                    port.save(update_fields=['descr'])
                except Port.DoesNotExist:
                    Port.objects.create(
                        num=port_num,
                        device=dev,
                        descr=port_text
                    )

        db_ports = Port.objects.filter(device=dev)
        db_ports = [TempPort(p.num, p.descr, None, True, p.pk) for p in db_ports]

        manager = dev.get_manager_klass()(dev.ip_address, dev.man_passw)
        ports = manager.get_ports()
        if ports is not None:
            ports = [TempPort(p.num, p.nm, p.st, False) for p in ports]
            res_ports = set(db_ports + ports)
        else:
            res_ports = db_ports

    except Device.DoesNotExist:
        messages.error(request, _('Device does not exist'))
        return redirect('devapp:group_list')
    except DeviceDBException as e:
        messages.error(request, e)
    except EasySNMPTimeoutError:
        messages.error(request, _('wait for a reply from the SNMP Timeout'))
    return render(request, 'devapp/manage_ports/add_ports.html', {
        'ports': res_ports,
        'dev': dev
    })


@login_required
@permission_required('devapp.delete_port')
def delete_single_port(request, grp, did, portid):
    try:
        if request.method == 'POST':
            if request.POST.get('confirm') == 'yes':
                Port.objects.get(pk=portid).delete()
                messages.success(request, _('Port successfully removed'))
        else:
            return render_to_text('devapp/manage_ports/modal_del_port.html', {
                'grp': grp,
                'did': did,
                'port_id': portid
            }, request=request)
    except Port.DoesNotExist:
        messages.error(request, _('Port does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', grp, did)


@login_required
@permission_required('devapp.add_port')
def edit_single_port(request, grp, did, pid):
    try:
        port = Port.objects.get(pk=pid)
        if request.method == 'POST':
            frm = PortForm(request.POST, instance=port)
            if frm.is_valid():
                frm.save()
                messages.success(request, _('Port successfully saved'))
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
            return redirect('devapp:manage_ports', grp, did)

        frm = PortForm(instance=port)
        return render_to_text('devapp/manage_ports/modal_add_edit_port.html', {
            'port_id': pid,
            'did': did,
            'gid': grp,
            'form': frm
        }, request=request)
    except Port.DoesNotExist:
        messages.error(request, _('Port does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', grp, did)


@login_required
@permission_required('devapp.add_port')
def add_single_port(request, grp, did):
    try:
        device = Device.objects.get(pk=did)
        if request.method == 'POST':
            frm = PortForm(request.POST, instance=Port(device=device))
            if frm.is_valid():
                frm.save()
                messages.success(request, _('Port successfully saved'))
                return redirect('devapp:manage_ports', grp, did)
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
        else:
            frm = PortForm(initial={
                'num': request.GET.get('n'),
                'descr': request.GET.get('t')
            })
        return render_to_text('devapp/manage_ports/modal_add_edit_port.html', {
            'did': did,
            'gid': grp,
            'form': frm
        }, request=request)
    except Device.DoesNotExist:
        messages.error(request, _('Device does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', grp, did)


@login_required
@only_admins
def devview(request, did):
    ports = None
    uptime = 0
    dev = get_object_or_404(Device, id=did)
    template_name = 'ports.html'
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
    except DeviceDBException as e:
        messages.error(request, e)

    return render(request, 'devapp/custom_dev_page/'+template_name, {
        'dev': dev,
        'ports': ports,
        'uptime': uptime,
        'dev_accs': Abon.objects.filter(device=dev)
    })


@login_required
@only_admins
def toggle_port(request, did, portid, status=0):
    portid = int(portid)
    status = int(status)
    dev = get_object_or_404(Device, id=int(did))
    try:
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
    except EasySNMPTimeoutError:
        messages.error(request, _('wait for a reply from the SNMP Timeout'))
    return redirect('devapp:view', dev.user_group.pk if dev.user_group is not None else 0, did)


@login_required
@only_admins
def group_list(request):
    groups = AbonGroup.objects.all()
    return render(request, 'devapp/group_list.html', {
        'groups': groups
    })


@login_required
def search_dev(request):
    word = request.GET.get('s')
    if word is None:
        results = [{'id': 0, 'text': ''}]
    else:
        results = Device.objects.filter(Q(comment__icontains=word) | Q(ip_address=word))[:16]
        results = [{'id': dev.pk, 'text': "%s: %s" % (dev.ip_address, dev.comment)} for dev in results]
    return HttpResponse(dumps(results, ensure_ascii=False))
