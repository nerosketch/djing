import re
from django.db.models import Q
from django.shortcuts import render
from django.utils.html import escape
from abonapp.models import Abon


def replace_without_case(orig, old, new):
    return re.sub(old, new, orig, flags=re.IGNORECASE)


def home(request):
    s = request.GET.get('s')

    if s:
        query = Q(fio__icontains=s) | Q(username__icontains=s) | Q(telephone__icontains=s) | Q(ip_address=s)
        abons = Abon.objects.filter(query)
    else:
        abons = []

    for abn in abons:
        abn.fio = replace_without_case(escape(abn.fio), s, "<b>%s</b>" % s)
        abn.username = replace_without_case(escape(abn.username), s, "<b>%s</b>" % s)
        abn.telephone = replace_without_case(escape(abn.telephone), s, "<b>%s</b>" % s)

    return render(request, 'searchapp/index.html', {
        'abons': abons,
        's': s
    })
