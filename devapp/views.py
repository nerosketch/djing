# -*- coding: utf-8 -*-
import re
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _, gettext
from easysnmp import EasySNMPTimeoutError, EasySNMPError
from django.views.generic import DetailView

from devapp.base_intr import DeviceImplementationError
from mydefs import res_success, res_error, only_admins, safe_int
from abonapp.models import Abon
from group_app.models import Group
from accounts_app.models import UserProfile
from django.conf import settings
from guardian.decorators import permission_required_or_403 as permission_required
from guardian.shortcuts import get_objects_for_user
from chatbot.telebot import send_notify
from chatbot.models import ChatException
from jsonview.decorators import json_view
from djing import global_base_views, IP_ADDR_REGEX, ping, get_object_or_None
from .models import Device, Port, DeviceDBException, DeviceMonitoringException
from .forms import DeviceForm, PortForm


class BaseDeviceListView(global_base_views.BaseListWithFiltering):
    http_method_names = ['get']
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


@method_decorator([login_required, only_admins], name='dispatch')
class DevicesListView(global_base_views.OrderingMixin, BaseDeviceListView):
    context_object_name = 'devices'
    template_name = 'devapp/devices.html'

    def get_queryset(self):
        group_id = safe_int(self.kwargs.get('group_id'))
        queryset = Device.objects.filter(group__pk=group_id) \
            .select_related('group') \
            .only('comment', 'mac_addr', 'devtype', 'group', 'pk', 'ip_address')
        return queryset

    def get_context_data(self, **kwargs):
        group_id = safe_int(self.kwargs.get('group_id'))
        context = super(DevicesListView, self).get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, pk=group_id)
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super(DevicesListView, self).dispatch(request, *args, **kwargs)
        except (DeviceDBException, DeviceMonitoringException) as e:
            messages.error(request, e)
            response = HttpResponse('Error')
        return response


@method_decorator([login_required, only_admins], name='dispatch')
class DevicesWithoutGroupsListView(global_base_views.OrderingMixin, BaseDeviceListView):
    context_object_name = 'devices'
    template_name = 'devapp/devices_null_group.html'
    queryset = Device.objects.filter(group=None).only('comment', 'devtype', 'pk', 'ip_address')


@login_required
@permission_required('devapp.delete_device')
def devdel(request, device_id):
    try:
        dev = Device.objects.get(pk=device_id)
        back_url = resolve_url('devapp:devs', group_id=dev.group.pk if dev.group else 0)
        dev.delete()
        return res_success(request, back_url)
    except Device.DoesNotExist:
        return res_error(request, _('Delete failed'))
    except DeviceDBException as e:
        return res_error(request, e)


@login_required
@permission_required('devapp.can_view_device')
def dev(request, group_id, device_id=0):
    device_group = get_object_or_404(Group, pk=group_id)
    if not request.user.has_perm('group_app.can_view_group', device_group):
        raise PermissionDenied
    devinst = get_object_or_404(Device, id=device_id) if device_id != 0 else None
    already_dev = None

    if request.method == 'POST':
        if device_id == 0:
            if not request.user.has_perm('devapp.add_device'):
                raise PermissionDenied
        else:
            if not request.user.has_perm('devapp.change_device'):
                raise PermissionDenied
        try:
            frm = DeviceForm(request.POST, instance=devinst)
            if frm.is_valid():

                # check if that device is exist
                try:
                    already_dev = Device.objects.exclude(pk=device_id).get(mac_addr=request.POST.get('mac_addr'))
                    if already_dev.group:
                        messages.warning(request, _('You have redirected to existing device'))
                        return redirect('devapp:view', already_dev.group.pk, already_dev.pk)
                    else:
                        messages.warning(request, _('Please attach group for device'))
                        return redirect('devapp:fix_device_group', already_dev.pk)
                except Device.DoesNotExist:
                    pass

                # else update device info
                ndev = frm.save()
                # change device info in dhcpd.conf
                ndev.update_dhcp()
                messages.success(request, _('Device info has been saved'))
                return redirect('devapp:edit', ndev.group.pk, ndev.pk)
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
        except IntegrityError as e:
            if 'unique constraint' in str(e):
                messages.error(request, _('Duplicate user and port: %s') % e)
            else:
                messages.error(request, e)
    else:
        if devinst is None:
            frm = DeviceForm(initial={
                'group': device_group,
                'devtype': request.GET.get('t'),
                'mac_addr': request.GET.get('mac'),
                'comment': request.GET.get('c'),
                'ip_address': request.GET.get('ip'),
                'man_passw': getattr(settings, 'DEFAULT_SNMP_PASSWORD', ''),
                'snmp_item_num': request.GET.get('n') or 0
            })
        else:
            frm = DeviceForm(instance=devinst)

    if devinst is None:
        parent_device_id = request.GET.get('pdev')
        return render(request, 'devapp/add_dev.html', {
            'form': frm,
            'group': device_group,
            'already_dev': already_dev,
            'selected_parent_dev': get_object_or_None(Device, pk=parent_device_id)
        })
    else:
        return render(request, 'devapp/dev.html', {
            'form': frm,
            'dev': devinst,
            'selected_parent_dev': devinst.parent_dev,
            'group': device_group,
            'already_dev': already_dev
        })


@login_required
@permission_required('devapp.change_device')
def manage_ports(request, device_id):
    try:
        dev = Device.objects.get(pk=device_id)
        if dev.group is None:
            messages.error(request, _('Device does not have a group, please fix that'))
            return redirect('devapp:fix_device_group', dev.pk)
        ports = Port.objects.filter(device=dev).annotate(num_abons=Count('abon'))

    except Device.DoesNotExist:
        messages.error(request, _('Device does not exist'))
        return redirect('devapp:group_list')
    except DeviceDBException as e:
        messages.error(request, e)
    return render(request, 'devapp/manage_ports/list.html', {
        'ports': ports,
        'dev': dev
    })


@method_decorator([login_required, only_admins], name='dispatch')
class ShowSubscriberOnPort(global_base_views.RedirectWhenErrorMixin, DetailView):
    template_name = 'devapp/manage_ports/modal_show_subscriber_on_port.html'
    http_method_names = ['get']

    def get_object(self, queryset=None):
        dev_id = self.kwargs.get('device_id')
        port_id = self.kwargs.get('port_id')
        try:
            obj = Abon.objects.get(device_id=dev_id, dev_port_id=port_id)
        except Abon.DoesNotExist:
            raise Http404(gettext('Subscribers on port does not exist'))
        except Abon.MultipleObjectsReturned:
            errmsg = gettext('More than one subscriber on device port')
            # messages.error(self.request, errmsg)
            raise global_base_views.RedirectWhenError(
                resolve_url('devapp:fix_port_conflict', group_id=self.kwargs.get('group_id'), device_id=dev_id,
                            port_id=port_id),
                errmsg
            )
        return obj


@login_required
@permission_required('devapp.add_port')
def add_ports(request, device_id):
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
            return "p:%d\tT:%s" % (self.pid, self.text)

    try:
        res_ports = list()
        dev = Device.objects.get(pk=device_id)
        if dev.group is None:
            messages.error(request, _('Device does not have a group, please fix that'))
            return redirect('devapp:fix_device_group', dev.pk)
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

        manager = dev.get_manager_object()
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
def delete_single_port(request, group_id, device_id, portid):
    try:
        if request.method == 'POST':
            if request.POST.get('confirm') == 'yes':
                Port.objects.get(pk=portid).delete()
                messages.success(request, _('Port successfully removed'))
        else:
            return render_to_text('devapp/manage_ports/modal_del_port.html', {
                'grp': group_id,
                'did': device_id,
                'port_id': portid
            }, request=request)
    except Port.DoesNotExist:
        messages.error(request, _('Port does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', group_id, device_id)


@login_required
@permission_required('devapp.add_port')
def edit_single_port(request, group_id, device_id, port_id):
    try:
        port = Port.objects.get(pk=port_id)
        if request.method == 'POST':
            frm = PortForm(request.POST, instance=port)
            if frm.is_valid():
                frm.save()
                messages.success(request, _('Port successfully saved'))
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
            return redirect('devapp:manage_ports', group_id, device_id)

        frm = PortForm(instance=port)
        return render_to_text('devapp/manage_ports/modal_add_edit_port.html', {
            'port_id': port_id,
            'did': device_id,
            'gid': group_id,
            'form': frm
        }, request=request)
    except Port.DoesNotExist:
        messages.error(request, _('Port does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', group_id, device_id)


@login_required
@permission_required('devapp.add_port')
def add_single_port(request, group_id, device_id):
    try:
        device = Device.objects.get(pk=device_id)
        if request.method == 'POST':
            frm = PortForm(request.POST, instance=Port(device=device))
            if frm.is_valid():
                frm.save()
                messages.success(request, _('Port successfully saved'))
                return redirect('devapp:manage_ports', group_id, device_id)
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
        else:
            frm = PortForm(initial={
                'num': request.GET.get('n'),
                'descr': request.GET.get('t')
            })
        return render_to_text('devapp/manage_ports/modal_add_edit_port.html', {
            'did': device_id,
            'gid': group_id,
            'form': frm
        }, request=request)
    except Device.DoesNotExist:
        messages.error(request, _('Device does not exist'))
    except DeviceDBException as e:
        messages.error(request, e)
    return redirect('devapp:manage_ports', group_id, device_id)


@login_required
@permission_required('devapp.can_view_device')
def devview(request, device_id):
    ports, manager = None, None
    dev = get_object_or_404(Device, id=device_id)

    if not dev.group:
        messages.warning(request, _('Please attach group for device'))
        return redirect('devapp:fix_device_group', dev.pk)

    template_name = 'ports.html'
    try:
        if dev.ip_address:
            if not ping(dev.ip_address):
                messages.error(request, _('Dot was not pinged'))
        if dev.man_passw:
            manager = dev.get_manager_object()
            ports = manager.get_ports()
            if len(ports) > 0 and isinstance(ports[0], Exception):
                messages.error(request, ports[0])
                ports = ports[1]
            template_name = manager.get_template_name()
        else:
            messages.warning(request, _('Not Set snmp device password'))
        return render(request, 'devapp/custom_dev_page/' + template_name, {
            'dev': dev,
            'ports': ports,
            'dev_accs': Abon.objects.filter(device=dev),
            'dev_manager': manager
        })
    except EasySNMPError as e:
        messages.error(request, "%s: %s" % (gettext('SNMP error on device'), e))
    except (DeviceDBException, DeviceImplementationError) as e:
        messages.error(request, e)
    return render(request, 'devapp/custom_dev_page/' + template_name, {
        'dev': dev
    })


@login_required
@permission_required('devapp.can_toggle_ports')
def toggle_port(request, device_id, portid, status=0):
    portid = int(portid)
    status = int(status)
    dev = get_object_or_404(Device, id=int(device_id))
    try:
        if ping(dev.ip_address):
            if dev.man_passw:
                manager = dev.get_manager_object()
                ports = manager.get_ports()
                if status:
                    ports[portid - 1].enable()
                else:
                    ports[portid - 1].disable()
            else:
                messages.warning(request, _('Not Set snmp device password'))
        else:
            messages.error(request, _('Dot was not pinged'))
    except EasySNMPTimeoutError:
        messages.error(request, _('wait for a reply from the SNMP Timeout'))
    except EasySNMPError as e:
        messages.error(request, 'EasySNMPError: %s' % e)
    return redirect('devapp:view', dev.group.pk if dev.group is not None else 0, device_id)


@method_decorator([login_required, only_admins], name='dispatch')
class GroupsListView(BaseDeviceListView):
    context_object_name = 'groups'
    template_name = 'devapp/group_list.html'
    model = Group

    def get_queryset(self):
        groups = super(GroupsListView, self).get_queryset()
        groups = get_objects_for_user(self.request.user, 'group_app.can_view_group', klass=groups,
                                      accept_global_perms=False)
        return groups


@login_required
def search_dev(request):
    word = request.GET.get('s')
    if word is None or word == '':
        results = [{'id': 0, 'text': ''}]
    else:
        results = Device.objects.filter(
            Q(comment__icontains=word) | Q(ip_address=word)
        ).only('pk', 'ip_address', 'comment')[:16]
        results = [{'id': dev.pk, 'text': "%s: %s" % (dev.ip_address or '', dev.comment)} for dev in results]
    return JsonResponse(results, json_dumps_params={'ensure_ascii': False}, safe=False)


@login_required
def fix_device_group(request, device_id):
    dev = get_object_or_404(Device, pk=device_id)
    try:
        if request.method == 'POST':
            frm = DeviceForm(request.POST, instance=dev)
            if frm.is_valid():
                ch_dev = frm.save()
                if ch_dev.group:
                    messages.success(request, _('Device fixed'))
                    return redirect('devapp:devs', ch_dev.group.pk)
                else:
                    messages.error(request, _('Please attach group for device'))
            else:
                messages.error(request, _('Form is invalid, check fields and try again'))
        else:
            frm = DeviceForm(instance=dev)
    except ValueError:
        return HttpResponse('ValueError')
    return render(request, 'devapp/fix_dev_group.html', {
        'form': frm,
        'dev': dev,
        'selected_parent_dev': dev.parent_dev
    })


@login_required
def fix_onu(request):
    mac = request.GET.get('cmd_param')
    status = 1
    text = '<span class="glyphicon glyphicon-exclamation-sign"></span>'
    try:
        onu = Device.objects.get(mac_addr=mac, devtype='On')
        parent = onu.parent_dev
        if parent is not None:
            manobj = parent.get_manager_object()
            ports = manobj.get_list_keyval('.1.3.6.1.4.1.3320.101.10.1.1.3')
            text = '<span class="glyphicon glyphicon-ok"></span> <span class="hidden-xs">%s</span>' % \
                   (_('Device with mac address %(mac)s does not exist') % {'mac': mac})
            for srcmac, snmpnum in ports:
                # convert bytes mac address to str presentation mac address
                real_mac = ':'.join(['%x' % ord(i) for i in srcmac])
                if mac == real_mac:
                    onu.snmp_item_num = snmpnum
                    onu.save(update_fields=['snmp_item_num'])
                    status = 0
                    text = '<span class="glyphicon glyphicon-ok"></span> <span class="hidden-xs">%s</span>' % _('Fixed')
                    break
        else:
            text = text + '\n%s' % _('Parent device not found')
    except Device.DoesNotExist:
        pass
    return JsonResponse({
        'status': status,
        'dat': text
    })


@login_required
def fix_port_conflict(request, group_id, device_id, port_id):
    dev_group = get_object_or_404(Group, pk=group_id)
    device = get_object_or_404(Device, pk=device_id)
    port = get_object_or_404(Port, pk=port_id)
    abons = Abon.objects.filter(device__id=device_id, dev_port__id=port_id)
    return render(request, 'devapp/manage_ports/fix_abon_device.html', {
        'abons': abons,
        'group': dev_group,
        'device': device,
        'port': port
    })


class OnDeviceMonitoringEvent(global_base_views.AllowedSubnetMixin, global_base_views.HashAuthView):
    #
    # Api view for monitoring devices
    #
    http_method_names = ['get']

    @method_decorator(json_view)
    def get(self, request):
        try:
            dev_ip = request.GET.get('ip')
            dev_status = request.GET.get('status')

            if dev_ip is None or dev_ip == '':
                return {'text': 'ip does not passed'}

            if not bool(re.match(IP_ADDR_REGEX, dev_ip)):
                return {'text': 'ip address %s is not valid' % dev_ip}

            device_down = Device.objects.filter(ip_address=dev_ip).first()
            if device_down is None:
                return {'text': 'Devices with ip %s does not exist' % dev_ip}

            if dev_status == 'UP':
                device_down.status = 'up'
                notify_text = 'Device %(device_name)s is up'
            elif dev_status == 'DOWN':
                device_down.status = 'dwn'
                notify_text = 'Device %(device_name)s is down'
            elif dev_status == 'UNREACHABLE':
                device_down.status = 'unr'
                notify_text = 'Device %(device_name)s is unreachable'
            else:
                device_down.status = 'und'
                notify_text = 'Device %(device_name)s getting undefined status code'

            device_down.save(update_fields=['status'])

            if not device_down.is_noticeable:
                return {'text': 'Notification for %s is unnecessary' % device_down.ip_address}

            recipients = UserProfile.objects.get_profiles_by_group(device_down.group.pk)
            names = list()

            for recipient in recipients:
                send_notify(
                    msg_text=gettext(notify_text) % {
                        'device_name': "%s %s" % (device_down.ip_address, device_down.comment)
                    },
                    account=recipient,
                    tag='devmon'
                )
                names.append(recipient.username)
            return {
                'text': 'notification successfully sent',
                'recipients': names
            }
        except ChatException as e:
            return {
                'text': str(e)
            }


class NagiosObjectsConfView(global_base_views.AuthenticatedOrHashAuthView):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        from transliterate import translit
        confs = list()

        def norm_name(name: str, replreg=re.compile(r'\W{1,255}', re.IGNORECASE)):
            return replreg.sub('', name)

        for dev in Device.objects.exclude(Q(ip_address=None) | Q(ip_address='127.0.0.1')) \
                .select_related('parent_dev') \
                .only('ip_address', 'comment', 'parent_dev'):
            host_name = norm_name("%d%s" % (dev.pk, translit(dev.comment, language_code='ru', reversed=True)))
            conf = None
            if dev.devtype == 'On':
                if dev.parent_dev:
                    host_addr = dev.parent_dev.ip_address
                    conf = self.templ_onu(host_name, host_addr, snmp_item=dev.snmp_item_num or None)
                else:
                    if dev.ip_address:
                        host_addr = dev.ip_address
                        conf = self.templ_onu(host_name, host_addr, snmp_item=dev.snmp_item_num or None)
            else:
                parent_host_name = norm_name("%d%s" % (
                    dev.parent_dev.pk, translit(dev.parent_dev.comment, language_code='ru', reversed=True)
                )) if dev.parent_dev else None
                conf = self.templ(host_name, host_addr=dev.ip_address, parent_host_name=parent_host_name)
            if conf is not None:
                confs.append(conf)
        response = HttpResponse(''.join(confs), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="objects.cfg"'
        return response

    @staticmethod
    def templ(host_name: str, host_addr: str, parent_host_name: str):
        return '\n'.join([
            "define host{",
            "\tuse				generic-switch",
            "\thost_name		%s" % host_name,
            "\taddress			%s" % host_addr,
            "\tparents			%s" % parent_host_name if parent_host_name is not None else '',
            "}\n"
        ])

    @staticmethod
    def templ_onu(host_name: str, host_addr: str, snmp_item: int):
        return '\n'.join([
            "define host{",
            "\tuse				device-onu",
            "\thost_name		%s" % host_name,
            "\taddress			%s" % host_addr,
            "\t_snmp_item		%d" % snmp_item if snmp_item is not None else '',
            "}\n"
        ])
