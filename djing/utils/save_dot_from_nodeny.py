#!/bin/env python2
# coding=utf-8

import os
from json import load
import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from devapp.models import Device

    with open('../../places.json', 'r') as f:
        dat = load(f)

    for dt in dat:
        if dt['descr']:
            dt['descr']=dt['descr'].replace('10.15.', '10.115.')
        dt['loc']=dt['loc'].encode('utf8')
        try:
            dev = Device.objects.get(ip_address=dt['descr'])
        except Device.DoesNotExist:
            dev = Device(
                ip_address=dt['descr']
            )
        dev.comment=dt['loc']
        dev.save()
        print(dt['descr'], dt['loc'], dev)
