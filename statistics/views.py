from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from djing.lib.decorators import only_admins


@login_required
@only_admins
def home(request):
    return render(request, 'statistics/index.html')
