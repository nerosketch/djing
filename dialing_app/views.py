from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from guardian.decorators import permission_required_or_403 as permission_required
from django.db.models import Q

from abonapp.models import Abon
from mydefs import only_admins, pag_mn
from .models import AsteriskCDR


@login_required
@permission_required('dialing_app.change_asteriskcdr')
@only_admins
def home(request):
    logs = AsteriskCDR.objects.exclude(userfield='request').order_by('-calldate')
    logs = pag_mn(request, logs)
    title = _('Last calls')
    return render(request, 'index.html', {
        'logs': logs,
        'title': title
    })


@login_required
@only_admins
def to_abon(request, tel):
    abon = Abon.objects.filter(telephone=tel)
    abon_count = abon.count()
    if abon_count > 1:
        messages.warning(request, _('Multiple users with the telephone number'))
    elif abon_count == 0:
        messages.error(request, _('User with the telephone number not found'))
        return redirect('dialapp:home')
    abon = abon[0]
    if abon.group:
        return redirect('abonapp:abon_home', gid=abon.group.pk, uid=abon.pk)
    else:
        return redirect('abonapp:group_list')


@login_required
@only_admins
def vmail(request):
    title = _('Voice mail')
    cdr = AsteriskCDR.objects.filter(userfield='request').order_by('-calldate')
    cdr = pag_mn(request, cdr)
    return render(request, 'vmail.html', {
        'title': title,
        'vmessages': cdr
    })


@login_required
@only_admins
def vfilter(request):
    s = request.GET.get('s')
    cdr_q = Q(src__icontains=s) | Q(dst__icontains=s)
    cdr = AsteriskCDR.objects.filter(cdr_q)
    return render(request, 'index.html', {
        'logs': cdr,
        'title': _('Find dials'),
        's': s
    })

