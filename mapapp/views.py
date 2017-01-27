from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.gis.shortcuts import render_to_text
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.serializers import serialize
from .models import Dot
from .forms import DotForm
from mydefs import pag_mn


@login_required
def home(request):
    dots = Dot.objects.all()
    return render(request, 'maps/ya_index.html', {
        'dots': dots
    })


@login_required
def options(request):
    dots = Dot.objects.all()
    dots = pag_mn(request, dots)
    return render(request, 'maps/options.html', {
        'dots': dots
    })


@login_required
def dot(request, did=0):
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
            frm = DotForm(request.POST, instance=dot)
            if frm.is_valid():
                frm.save()
                messages.success(request, 'Точка топологии сохранена')
            else:
                messages.error(request, 'ошибки в форме')
        else:
            frm = DotForm(instance=dot)

        return render(request, 'maps/dot.html', {
            'dot': dot,
            'form': frm
        })

    except Dot.DoesNotExist:
        messages.error(request, 'Эта точка топологии не существует')
        return redirect('mapapp:options')


@login_required
@permission_required('mapapp.delete_dot')
def remove(request, did):
    try:
        dot = Dot.objects.get(id=did)
        title = dot.title
        dot.delete()
        messages.success(request, "Точка топологии '%s' успешно удалена" % title)
    except Dot.DoesNotExist:
        messages.error(request, 'Эта точка топологии не существует')
    return redirect('mapapp:options')


def get_dots(request):
    dots = Dot.objects.all()
    return HttpResponse(serialize('json', dots, ensure_ascii=False), content_type='application/json')


@login_required
@permission_required('mapapp.add_dot')
def modal_add_dot(request):
    if request.method == 'POST':
        coords = request.POST.get('coords')
        title = request.POST.get('title')
        lat, lon = coords.split(',')
        print(lat, lon)
        Dot.objects.create(
            title=title,
            latitude=float(lat),
            longitude=float(lon)
        )
        return redirect('mapapp:home')
    else:
        coords = request.GET.get('coords')
    return render_to_text('maps/modal_add_dot.html', {
        'coords': coords
    }, request=request)
