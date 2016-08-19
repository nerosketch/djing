from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from models import Dot
from json import dumps


@login_required
def home(request):
    return render(request, 'maps/index.html')



def get_dots(r):
    dots = Dot.objects.all()
    return HttpResponse(dumps({
        'dots': map(lambda d: (d.id, d.posX, d.posY, d.title), dots)
    }))
