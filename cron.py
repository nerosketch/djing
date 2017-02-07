#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from abonapp.models import Abon
    from agent import Transmitter, AbonStruct, TariffStruct, NasFailedResult

    tm = Transmitter()
    users = Abon.objects.all()
    for user in users:
        if user.ip_address is None:
            continue
        cur_tar = user.active_tariff()
        if cur_tar is None:
            continue
        ab = AbonStruct(
            uid=user.id,
            ip=user.ip_address.int_ip(),
            tariff=TariffStruct(
                tariff_id=cur_tar.id,
                speedIn=cur_tar.speedIn,
                speedOut=cur_tar.speedOut
            )
        )
        # обновляем абонента на NAS
        mikroid = tm._find_queue('uid%d' % user.id)
        mikroid = mikroid['=.id'].replace('*', '')
        try:
            tm.update_user(ab)
        except NasFailedResult:
            tm.add_user(ab)
        # если не активен то приостановим услугу
        if user.is_active:
            tm.start_user(mikroid)
        else:
            tm.pause_user(mikroid)
        tm.update_user(ab)
