# -*- coding:utf-8 -*-
import socket
import struct
from json import loads, dumps
from abc import ABCMeta, abstractmethod


class Serializer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _serializable_obj(self):
        """Вернуть словарь для сериализации"""

    def serialize(self):
        return dumps(self._serializable_obj())

    @abstractmethod
    def deserialize(self, *args):
        """Надо обязательно этот метод реализовать, он много где используется.
        Из JSON создать объект класса где реализуется метод"""


def serialize_tariffs(tariffs):
    dt = map(lambda trf: trf._serializable_obj(), tariffs)
    return dumps({'tariffs': dt})


def deserialize_tariffs(dat):
    dat = loads(dat) if type(dat) == str else dat
    # Распаковываем из JSON массива dat['tariffs'] объекты через метод deserialize
    return map(lambda tariff: Tariff().deserialize(tariff), dat['tariffs'])


def serialize_abonents(abonents):
    dt = map(lambda abn: abn._serializable_obj(), abonents)
    return dumps({'subscribers': dt})


def deserialize_abonents(dat, tariffs):
    dat = loads(dat) if type(dat) == str else dat
    # Распаковываем из JSON массива dat['subscribers'] объекты через метод deserialize
    return map(lambda abon: Abonent().deserialize(abon, tariffs), dat['subscribers'])


class Tariff(Serializer):
    tid = 0
    speedIn = 0.0
    speedOut = 0.0

    def __init__(self, tariff_id=None, speed_in=None, speed_out=None):
        self.tid = tariff_id
        self.speedOut = speed_out
        self.speedIn = speed_in

    def is_active(self):
        """возвращает активность тарифа. Если он не активен то пропустить"""
        return True

    def _serializable_obj(self):
        return {
            'id': self.tid,
            'speedIn': self.speedIn,
            'speedOut': self.speedOut
        }

    def deserialize(self, dump):
        inf = loads(dump) if type(dump) == str else dump
        self.speedIn = float(inf['speedIn'])
        self.speedOut = float(inf['speedOut'])
        self.tid = int(inf['id'])
        return self


class Abonent(Serializer):
    uid = 0
    tariff = Tariff()
    ip = 0xffffffff

    # Включён-ли абонент
    is_active = True

    def __init__(self, uid=None, ip=None, tariff=None):
        self.ip = ip
        self.uid = uid
        self.tariff = tariff

    def ip_str(self):
        # int2ip, Example out '127.0.0.1'
        return socket.inet_ntoa(struct.pack("!I", self.ip))

    def _serializable_obj(self):
        return {
            'id': self.uid,
            'is_active': self.is_active,
            'ip': self.ip,
            'tarif_id': self.tariff.tid if self.tariff else 0
        }

    def deserialize(self, dump, tariffs):
        inf = loads(dump) if type(dump) == str else dump
        self.uid = int(inf['id'])
        self.is_active = bool(inf['is_active'])
        self.ip = int(inf['ip'])

        tarif_id = int(inf['tarif_id'])
        dbtrf = filter(lambda trf: trf.tid == tarif_id, tariffs)
        if len(dbtrf) > 0:
            self.tariff = dbtrf[0]
        else:
            self.tariff = None
        return self


class EventNAS(Serializer):

    # Type Of Action
    toa = 0

    # id of object
    id = 0

    # extended data
    dt = object()

    def __init__(self, type_action=None, obj_id=None, ext_data=None):
        self.toa = type_action
        self.id = obj_id
        self.dt = ext_data

    def _serializable_obj(self):
        if self.dt:
            return {'toa': self.toa, 'id': self.id, 'dt': self.dt}
        else:
            return {'toa': self.toa, 'id': self.id}

    def deserialize(self, dump):
        print dump
        inf = loads(dump) if type(dump) == str else dump
        self.toa = int(inf['toa'])
        self.id = int(inf['id'])
        self.dt = inf.get('dt')
        return self
