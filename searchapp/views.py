import re
from django.db.models import Q
from django.shortcuts import render
from django.utils.html import escape
from abonapp.models import Abon
from mydefs import ip_addr_regex


def replace_without_case(orig, old, new):
    return re.sub(old, new, orig, flags=re.IGNORECASE)


def home(request):
    s = request.GET.get('s')
    s = s.replace('+', '')

    if s:
        if bool(re.match(ip_addr_regex, s)):
            abons = Abon.objects.filter(ip_address=s)
        else:
            abons = Abon.objects.filter(
                Q(fio__icontains=s) | Q(username__icontains=s) | Q(telephone__icontains=s)
            )
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
