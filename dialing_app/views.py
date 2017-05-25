from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

from abonapp.models import Abon
from mydefs import only_admins, pag_mn
from .models import AsteriskCDR


@login_required
@only_admins
def home(request):
    logs = AsteriskCDR.objects.all()
    logs = pag_mn(request, logs)
    return render(request, 'index.html', {
        'logs': logs
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

