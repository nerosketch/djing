#!/bin/env python3
# coding=utf-8

import os
from json import load
import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from abonapp.models import Abon, AbonGroup, AbonTariff
    from ip_pool.models import IpPoolItem
    from tariff_app.models import Tariff
    from accounts_app.models import UserProfile

    with open('dump_pshen.json', 'r') as f:
        dat = load(f)

    #for dt in dat['groups']:
    #    try:
    #        grp = AbonGroup.objects.get(title=dt['gname'])
    #    except AbonGroup.DoesNotExist:
    #        grp = AbonGroup(title=dt['gname'])
    #    grp.save()
    #    dt['obj'] = grp

    grp = AbonGroup.objects.get(id=43)
    pshn_trf = Tariff.objects.get(id=3)
    print(pshn_trf)
    iam = UserProfile.objects.get(id=1)
    for dt in dat['users']:
        #grp = [gr for gr in dat['groups'] if dt['grp']==gr['gid']]
        #grp = grp[0]['obj'] if len(grp)>0 else None
        try:
            abon = Abon.objects.get(username=dt['name'])
        except Abon.DoesNotExist:
            abon = Abon(username=dt['name'])
        try:
            ip_addr = IpPoolItem.objects.get(ip=dt['ip'])
        except IpPoolItem.DoesNotExist:
            ip_addr = None
        abon.fio = dt['fio']
        abon.telephone=dt['tel']
        abon.house=dt['addr']
        abon.group=grp
        abon.ballance=dt['balance']
        abon.ip_address=ip_addr
        abon.save()

        abtrfs =  AbonTariff.objects.filter(abon=abon)
        if abtrfs.count() > 0:
            abtrf = abtrfs[0]
        else:
            abtrf = AbonTariff()
        abtrf.abon = abon
        abtrf.tariff = pshn_trf
        abtrf.save()
        abtrf.activate(iam)
        print(abon.username, abon.fio, abon.group, ip_addr)

