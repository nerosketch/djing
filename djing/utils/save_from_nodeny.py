#!/bin/env python3
# coding=utf-8

import os
from json import load
import django
from django.utils import timezone
from django.core.exceptions import ValidationError
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from abonapp.models import Abon, AbonGroup, AbonRawPassword, AbonStreet, AbonTariff, Opt82
from ip_pool.models import IpPoolItem
from tariff_app.models import Tariff


class DumpService(object):
    price = 0.0
    speedIn = 0.0
    speedOut = 0.0

    def __init__(self, obj=None):
        if obj is None: return
        self.title = obj['title']
        self.price = obj['price']
        self.description = obj['description']
        self.speedIn = int(obj['param']['speed_in1']) / 1000000
        self.speedOut = int(obj['param']['speed_out1']) / 1000000

    @staticmethod
    def build_from_db(obj):
        self = DumpService()
        self.title = obj.title
        self.price = obj.amount
        self.description = obj.descr
        self.speedIn = obj.speedIn
        self.speedOut = obj.speedOut
        return self

    def __eq__(self, other):
        assert isinstance(other, DumpService)
        print('DBG:', type(other.price), other.price, type(self.price), self.price)
        r = self.price == other.price
        r = r and self.speedIn == other.speedIn
        r = r and self.speedOut == other.speedOut
        return r

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "%s; '%.2f', %f %f" % (self.title, self.price, self.speedIn, self.speedOut)


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
        self.ip = obj['ip'] if obj['ip'] != '' else None
        self.balance = obj['balance']
        self.passw = obj['passw']
        if obj['opt82']['dev_mac'] is not None and obj['opt82']['dev_port'] is not None:
            self.opt82 = {
                'dev_mac': obj['opt82']['dev_mac'],
                'dev_port': obj['opt82']['dev_port']
            }

        if obj['service'] is not None:
            self.service = DumpService(obj['service'])
        else:
            self.service = None

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
        if obj.group is None:
            self.grp = None
        else:
            self.grp = obj.group.pk
        if obj.ip_address is None:
            self.ip = None
        else:
            self.ip = obj.ip_address
        self.balance = obj.ballance
        try:
            raw_passw = AbonRawPassword.objects.get(account=obj)
        except AbonRawPassword.DoesNotExist:
            raw_passw = ''
        self.passw = raw_passw
        srv = obj.active_tariff()
        if srv is not None:
            self.service = DumpService.build_from_db(srv)
        else:
            self.service = None
        if obj.opt82 is not None and obj.opt82.mac is not None and obj.opt82.port is not None:
            self.opt82 = {
                'dev_mac': obj.opt82.mac,
                'dev_port': obj.opt82.port
            }
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


def add_service_if_not_exist(service):
    assert isinstance(service, DumpService)
    try:
        obj = Tariff.objects.get(speedIn=service.speedIn, speedOut=service.speedOut, amount=service.price)
    except Tariff.DoesNotExist:
        obj = Tariff.objects.create(
            title=service.title,
            descr=service.description,
            speedIn=service.speedIn,
            speedOut=service.speedOut,
            amount=service.price,
            calc_type='Dp'
        )
    return obj


def add_raw_password_if_not_exist(acc, raw_passw):
    try:
        psw = AbonRawPassword.objects.get(account=acc)
        #if psw != raw_passw:
        #    psw.passw_text = raw_passw
        #    psw.save(update_fields=['passw_text'])
    except AbonRawPassword.DoesNotExist:
        psw = AbonRawPassword.objects.create(account=acc, passw_text=raw_passw)
    return psw


def add_opt82_if_not_exist(mac, port):
    print(mac, port)
    try:
        opt82 = Opt82.objects.get(mac=mac, port=port)
    except Opt82.DoesNotExist:
        opt82 = Opt82.objects.create(mac=mac, port=port)
    return opt82


def load_users(obj, group):
    if len(obj) < 1:
        return
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
            abon = add_user(dump_abon, group)
        if abon is None:
            raise Exception("Чё за херня!? Не создался абонент")

        abon_service_from_dump = dump_abon.service
        if abon_service_from_dump is None:
            continue
        abon_service = add_service_if_not_exist(abon_service_from_dump)
        try:
            AbonTariff.objects.get(abon=abon, tariff=abon_service)
        except AbonTariff.DoesNotExist:
            calc_obj = abon_service.get_calc_type()(abon_service)
            AbonTariff.objects.create(
                abon=abon,
                tariff=abon_service,
                time_start=timezone.now(),
                deadline=calc_obj.calc_deadline()
            )
        try:
            if hasattr(dump_abon, 'opt82'):
                abon.opt82 = add_opt82_if_not_exist(dump_abon.opt82['dev_mac'], dump_abon.opt82['dev_port'])
                abon.save(update_fields=['opt82'])
        except ValidationError as e:
            print('\t', e)


def add_user(obj, user_group):
    assert isinstance(obj, DumpAbon)
    street = None
    ip = None
    try:
        if obj.ip is not None:
            ip = IpPoolItem.objects.get(ip=obj.ip)
        street = AbonStreet.objects.get(name=obj.street, group=user_group)
    except IpPoolItem.DoesNotExist:
        if obj.ip is not None:
            ip = IpPoolItem.objects.create(ip=obj.ip)
    except AbonStreet.DoesNotExist:
        street = AbonStreet.objects.create(name=obj.street, group=user_group)

    abon = Abon()
    abon.username = obj.name
    abon.fio = obj.fio
    abon.telephone = obj.tel
    abon.street = street
    abon.house = obj.house
    abon.birth_day = obj.birth
    abon.group = user_group
    abon.ip_address = ip
    abon.ballance = obj.balance
    abon.set_password(obj.passw)
    abon.save()
    add_raw_password_if_not_exist(abon, obj.passw)
    return abon


def update_user(db_abon, obj, user_group):
    assert isinstance(obj, DumpAbon)
    assert isinstance(db_abon, Abon)
    street = None
    ip = None
    try:
        if obj.ip is not None:
            ip = IpPoolItem.objects.get(ip=obj.ip)
        street = AbonStreet.objects.get(name=obj.street, group=user_group)
    except IpPoolItem.DoesNotExist:
        if obj.ip is not None:
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
    db_abon.set_password(obj.passw)
    db_abon.save()
    add_raw_password_if_not_exist(db_abon, obj.passw)


if __name__ == "__main__":

    with open('dump.json', 'r') as f:
        dat = load(f)

    for grp in dat:
        try:
            abgrp=AbonGroup.objects.get(title=grp['gname'])
        except AbonGroup.DoesNotExist:
            abgrp = AbonGroup.objects.create(
                title=grp['gname']
            )
        print(grp['gname'])
        load_users(grp['users'], abgrp)
