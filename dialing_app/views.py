from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from mydefs import only_admins
from .models import getModel


@login_required
@only_admins
def home(request):
    AsteriskCDR = getModel()
    logs = AsteriskCDR.objects.filter()
    return render(request, 'index.html', {
        'logs': logs
    })
