#!/bin/env python2
# coding=utf-8

import os
from json import load
import django
#from django.db.utils import IntegrityError


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from abonapp.models import Abon, AbonGroup

    with open('../../dump.json', 'r') as f:
        dat = load(f)

    for dt in dat['groups']:
        try:
            grp = AbonGroup.objects.get(title=dt['gname'])
        except AbonGroup.DoesNotExist:
            grp = AbonGroup(title=dt['gname'])
        grp.save()
        dt['obj'] = grp

    for dt in dat['users']:
        grp = filter(lambda gr: dt['grp']==gr['gid'], dat['groups'])
        grp = grp[0]['obj'] if len(grp)>0 else None
        try:
            abon = Abon.objects.get(username=dt['name'])
        except Abon.DoesNotExist:
            abon = Abon(username=dt['name'])
        abon.fio = dt['fio']
        abon.telephone=dt['tel']
        abon.address=dt['addr']
        abon.group=grp
        abon.save()
        print(abon.username, abon.fio, abon.group)
