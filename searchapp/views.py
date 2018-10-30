import re
from django.db.models import Q
from django.shortcuts import render
from django.utils.html import escape
from abonapp.models import Abon
from devapp.models import Device
from djing import MAC_ADDR_REGEX
from django.contrib.auth.decorators import login_required
from djing.lib.decorators import only_admins


def replace_without_case(orig, old, new):
    return re.sub(old, new, orig, flags=re.IGNORECASE)


@login_required
@only_admins
def home(request):
    s = request.GET.get('s')
    s = s.replace('+', '')

    if s:
        abons = Abon.objects.filter(
            Q(fio__icontains=s) | Q(username__icontains=s) | Q(telephone__icontains=s) |
            Q(additional_telephones__telephone__icontains=s) | Q(ip_address__icontains=s)
        )

        if re.match(MAC_ADDR_REGEX, s):
            devices = Device.objects.filter(mac_addr=s)
        else:
            devices = Device.objects.filter(Q(comment__icontains=s) | Q(ip_address__icontains=s))

    else:
        abons = ()
        devices = ()

    for abn in abons:
        abn.fio = replace_without_case(escape(abn.fio), s, "<b>%s</b>" % s)
        abn.username_display = replace_without_case(escape(abn.username), s, "<b>%s</b>" % s)
        abn.telephone = replace_without_case(escape(abn.telephone), s, "<b>%s</b>" % s)

    for dev in devices:
        dev.comment = replace_without_case(escape(dev.comment), s, "<b>%s</b>" % s)

    return render(request, 'searchapp/index.html', {
        'abons': abons,
        'devices': devices,
        's': s
    })
