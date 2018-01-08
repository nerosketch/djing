from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import Dot
from .forms import DotForm
from mydefs import pag_mn, safe_int
from devapp.models import Device
from guardian.decorators import permission_required
from abonapp.models import AbonGroup
from json import dumps


@login_required
def home(request):
    if not request.user.is_superuser:
        return redirect('/')
    dots = Dot.objects.all()
    groups = AbonGroup.objects.all()
    return render(request, 'maps/ya_index.html', {
        'dots': dots,
        'abon_groups': groups
    })


@login_required
def options(request):
    if not request.user.is_superuser:
        return redirect('/')
    dots = Dot.objects.all()
    dots = pag_mn(request, dots)
    return render(request, 'maps/options.html', {
        'dots': dots
    })


@login_required
def dot(request, did=0):
    if not request.user.is_superuser:
        return redirect('/')
    try:
        if did == 0:
            dot = Dot()
            if not request.user.has_perm('mapapp.add_dot'):
                raise PermissionDenied
        else:
            if not request.user.has_perm('mapapp.change_dot'):
                raise PermissionDenied
            dot = Dot.objects.get(id=did)

        if request.method == 'POST':
            frm = DotForm(request.POST, request.FILES, instance=dot)
            if frm.is_valid():
                new_dot = frm.save()
                messages.success(request, _('Map point has been saved'))
                return redirect('mapapp:edit_dot', new_dot.pk)
            else:
                messages.error(request, _('fix form errors'))
        else:
            frm = DotForm(instance=dot)

        return render(request, 'maps/dot.html', {
            'dot': dot,
            'form': frm
        })

    except Dot.DoesNotExist:
        messages.error(request, _('Map point does not exist'))
        return redirect('mapapp:options')


@login_required
@permission_required('mapapp.delete_dot')
def remove(request, did):
    try:
        dot = Dot.objects.get(id=did)
        title = dot.title
        dot.delete()
        messages.success(request, _("Map point '%(title)s' has been deleted") % {'title': title})
    except Dot.DoesNotExist:
        messages.error(request, _('Map point does not exist'))
    return redirect('mapapp:options')


@login_required
def get_dots(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('you have not super user')
    dots = Dot.objects.all().annotate(devcount=Count('devices'))
    res = [{
        'devcount': e.devcount,
        'latitude': e.latitude,
        'longitude': e.longitude,
        'title': e.title,
        'pk': e.pk
    } for e in dots]
    return HttpResponse(dumps(res), content_type='application/json')


@login_required
def modal_add_dot(request):
    if not request.user.has_perm('mapapp.add_dot'):
        return render_to_text('403_for_modal.html')
    if request.method == 'POST':
        frm = DotForm(request.POST, request.FILES)
        if frm.is_valid():
            new_dot = frm.save()
            res = {
                'latitude': new_dot.latitude,
                'longitude': new_dot.longitude,
                'title': new_dot.title,
                'pk': new_dot.pk
            }
        else:
            res = {
                'error': _('fix form errors')
            }
        return HttpResponse(dumps(res))
    else:
        coords = request.GET.get('coords')
        lat, lon = coords.split(',')
        frm = DotForm(initial={'latitude': lat, 'longitude': lon})
    return render_to_text('maps/modal_add_dot.html', {
        'coords': coords,
        'form': frm
    }, request=request)


@login_required
def preload_devices(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('you have not super user')
    grp = request.GET.get('grp')
    dot = request.GET.get('dot')
    #user_group = AbonGroup.objects.get(pk=grp)
    all_devices = Device.objects.filter(user_group__id=grp)
    dot_devices = Device.objects.filter(dot__id=dot)

    dot_devices_ids = [dev.pk for dev in dot_devices]

    ret = render_to_text('maps/preload_devices_tmpl.html', {
        'all_devices': all_devices,
        'dot_devices_ids': dot_devices_ids
    })
    return HttpResponse(ret, content_type='text/html')


@login_required
def dot_tooltip(request):
    if not request.user.is_superuser:
        return render_to_text('403_for_modal.html')
    d = request.GET.get('d')
    devs, dot = None, None
    try:
        dot = Dot.objects.get(id=d)
        devs = dot.devices.all()
        devs = Device.objects.wrap_monitoring_info(devs)
    except Dot.DoesNotExist:
        pass
    return render_to_text('maps/map_tooltip.html', {
        'devs': devs,
        'dot': dot
    })


@login_required
def add_dev(request, did):
    if not request.user.is_superuser:
        return redirect('/')
    groups = AbonGroup.objects.all()
    dot = get_object_or_404(Dot, pk=did)
    param_user_group = safe_int(request.GET.get('grp'))

    if request.method == 'POST':
        selected_devs = request.POST.getlist('dv')
        selected_user_group = safe_int(request.POST.get('selected_user_group'))

        existing_devs = Device.objects.filter(user_group__id=selected_user_group or param_user_group)
        if existing_devs.count() > 0:
            dot.devices.remove(*[dev.pk for dev in existing_devs])
        dot.devices.add(*selected_devs)

        url = resolve_url('mapapp:add_dev', did=dot.pk)
        return HttpResponseRedirect("%s?grp=%d" % (url, selected_user_group or param_user_group))
    else:
        existing_devs = Device.objects.filter(user_group=param_user_group)
    return render(request, 'maps/add_device.html', {
        'groups': groups,
        'dot': dot,
        'existing_devs': existing_devs,
        'grp': param_user_group,
        'dot_devices_ids': [dev.pk for dev in Device.objects.filter(dot=dot)]
    })


@login_required
def resolve_dots_by_group(request, grp_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden('you have not super user')
    devs = Device.objects.filter(user_group__id=grp_id)
    dots = Dot.objects.filter(devices__in=devs).annotate(devcount=Count('devices')).only('pk')
    res = [dot.pk for dot in dots]
    return HttpResponse(dumps(res), content_type='application/json')
