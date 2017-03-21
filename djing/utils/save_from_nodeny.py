#!/bin/env python3
# coding=utf-8

import os
from json import load
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from abonapp.models import Abon, AbonGroup, AbonRawPassword, AbonStreet
from ip_pool.models import IpPoolItem



class DumpAbon(object):

    def __init__(self, obj=None):
        if obj is None: return
        self.name = obj['name']
        self.fio = obj['fio']
        self.tel = obj['tel']
        self.street = obj['street']
        self.house = obj['house']
        self.birth = obj['birth']
        self.grp = obj['grp']
        self.ip = obj['ip']
        self.balance = obj['balance']
        self.passw = obj['passw']

    @staticmethod
    def build_from_django(obj):
        assert isinstance(obj, Abon)
        self = DumpAbon()
        self.name = obj.username
        self.fio = obj.fio
        self.tel = obj.telephone
        self.street = obj.street
        self.house = obj.house
        self.birth = obj.birth_day
        self.grp = obj.group.pk
        self.ip = obj.ip_address
        self.balance = obj.ballance
        try:
            raw_passw = AbonRawPassword.objects.get(account=obj)
        except AbonRawPassword.DoesNotExist:
            raw_passw = ''
        self.passw = raw_passw
        return self

    def __eq__(self, other):
        assert isinstance(other, DumpAbon)
        r = self.name == other.name
        r = r and self.name == other.name
        r = r and self.fio == other.fio
        r = r and self.tel == other.tel
        r = r and self.street == other.street
        r = r and self.house == other.house
        r = r and self.birth == other.birth
        r = r and self.grp == other.grp
        r = r and self.ip == other.ip
        r = r and self.balance == other.ballance
        return r

    def __ne__(self, other):
        return not self.__eq__(other)


def load_users(obj, group):
    for usr in obj:
        # абонент из дампа
        dump_abon = DumpAbon(usr)
        # абонент из биллинга
        print('\t', dump_abon.name, dump_abon.fio, dump_abon.ip)
        try:
            abon = Abon.objects.get(username=dump_abon.name)
            bl_abon = DumpAbon.build_from_django(abon)
            if bl_abon != dump_abon:
                update_user(abon, dump_abon, group)
        except Abon.DoesNotExist:
            # добавляем абонента
            add_user(dump_abon, group)


def add_user(obj, user_group):
    assert isinstance(obj, DumpAbon)
    street = None
    ip = None
    try:
        ip = IpPoolItem.objects.get(ip=obj.ip)
        street = AbonStreet.objects.get(name=obj.street)
    except IpPoolItem.DoesNotExist:
        ip = IpPoolItem.objects.create(ip=obj.ip)
    except AbonStreet.DoesNotExist:
        street = AbonStreet.objects.create(name=obj.street, group=user_group)

    Abon.objects.create(
        username=obj.name,
        fio=obj.fio,
        telephone=obj.tel,
        street=street,
        house=obj.house,
        birth_day=obj.birth,
        group = user_group,
        ip_address=ip,
        ballance=obj.balance
    )


def update_user(db_abon, obj, user_group):
    assert isinstance(obj, DumpAbon)
    assert isinstance(db_abon, Abon)
    street = None
    ip = None
    try:
        ip = IpPoolItem.objects.get(ip=obj.ip)
        street = AbonStreet.objects.get(name=obj.street, group=user_group)
    except IpPoolItem.DoesNotExist:
        if obj.ip:
            ip = IpPoolItem.objects.create(ip=obj.ip)
    except AbonStreet.DoesNotExist:
        street = AbonStreet.objects.create(name=obj.street, group=user_group)
    db_abon.fio = obj.fio
    db_abon.telephone = obj.tel
    db_abon.street = street
    db_abon.house = obj.house
    #db_abon.birth_day = datetime(obj.birth)
    db_abon.group = user_group
    db_abon.ip_address = ip
    db_abon.ballance = obj.balance
    db_abon.save()



if __name__ == "__main__":

    with open('dump.json', 'r') as f:
        dat = load(f)

    for grp in dat['groups']:
        try:
            abgrp=AbonGroup.objects.get(title=grp['gname'])
        except AbonGroup.DoesNotExist:
            abgrp = AbonGroup.objects.create(
                title=grp['gname']
            )
        print(grp['gname'])
        load_users(grp['users'], abgrp)
