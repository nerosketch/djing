# -*- coding: utf-8 -*-
from abc import ABCMeta
from typing import Iterable
from djing.lib import int2ip, ip2int


class BaseStruct(object, metaclass=ABCMeta):
    __slots__ = ()


class IpStruct(BaseStruct):
    __slots__ = ('__ip',)

    def __init__(self, ip):
        if type(ip) is int:
            self.__ip = ip
        else:
            self.__ip = ip2int(str(ip))

    def get_int(self):
        return self.__ip

    def __eq__(self, other):
        if not isinstance(other, IpStruct):
            raise TypeError('Instance must be IpStruct')
        return self.__ip == other.__ip

    def __int__(self):
        return self.__ip

    def __str__(self):
        return int2ip(self.__ip)

    def __hash__(self):
        return hash(self.__ip)


# Как обслуживается абонент
class TariffStruct(BaseStruct):
    __slots__ = ('tid', 'speedIn', 'speedOut')

    def __init__(self, tariff_id=0, speed_in=None, speed_out=None):
        self.tid = int(tariff_id)
        self.speedIn = speed_in or 0
        self.speedOut = speed_out or 0

    # Yes, if all variables is zeroed
    def is_empty(self):
        return self.tid == 0 and self.speedIn == 0 and self.speedOut == 0

    def __eq__(self, other):
        # не сравниваем id, т.к. тарифы с одинаковыми скоростями для NAS одинаковы
        # Да и иногда не удобно доставать из nas id тарифы из базы
        return self.speedIn == other.speedIn and self.speedOut == other.speedOut

    def __str__(self):
        return "Id=%d, speedIn=%.2f, speedOut=%.2f" % (self.tid, self.speedIn, self.speedOut)

    # нужно чтоб хеши тарифов In10,Out20 и In20,Out10 были разными
    # поэтому сначала float->str и потом хеш
    def __hash__(self):
        return hash(str(self.speedIn) + str(self.speedOut))


# Abon from database
class AbonStruct(BaseStruct):
    __slots__ = ('uid', 'ips', 'tariff', 'is_access', 'queue_id')

    def __init__(self, uid=0, ips=None, tariff=None, is_access=True):
        self.uid = int(uid or 0)
        if ips is None:
            self.ips = ()
        else:
            self.ips = tuple(IpStruct(ip) for ip in ips)
        self.tariff = tariff
        self.is_access = is_access
        self.queue_id = 0

    def __eq__(self, other):
        if not isinstance(other, AbonStruct):
            raise TypeError
        r = self.uid == other.uid and self.ips == other.ips
        r = r and self.tariff == other.tariff
        return r

    def __str__(self):
        return "uid=%d, ips=[%s], tariff=%s" % (self.uid, ';'.join(self.ips), self.tariff or '<No Service>')

    def __hash__(self):
        return hash(hash(self.ips) + hash(self.tariff)) if self.tariff is not None else 0


# Shape rule from NAS(Network Access Server)
class ShapeItem(BaseStruct):
    __slots__ = ('abon', 'sid')

    def __init__(self, abon, sid):
        self.abon = abon
        self.sid = sid

    def __eq__(self, other):
        if not isinstance(other, ShapeItem):
            raise TypeError
        return self.sid == other.sid and self.abon == other.abon


VectorAbon = Iterable[AbonStruct]
VectorTariff = Iterable[TariffStruct]
