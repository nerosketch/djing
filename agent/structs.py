# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from struct import pack, unpack, calcsize
from typing import Iterable
from .utils import int2ip, ip2int


class BaseStruct(object, metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        """привращаем инфу в бинарную строку"""

    @abstractmethod
    def deserialize(self, data, *args):
        """создаём объект из бинарной строки"""

    def __ne__(self, other):
        return not self == other


class IpStruct(BaseStruct):
    def __init__(self, ip):
        if type(ip) is int:
            self.__ip = ip
        else:
            self.__ip = ip2int(str(ip))

    def serialize(self):
        dt = pack("!I", int(self.__ip))
        return dt

    def deserialize(self, data, *args):
        dt = unpack("!I", data)
        self.__ip = int(dt[0])
        return self

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
    def __init__(self, tariff_id=0, speedIn=None, speedOut=None):
        self.tid = int(tariff_id)
        self.speedIn = float(speedIn if speedIn is not None else 0.001)
        self.speedOut = float(speedOut if speedOut is not None else 0.001)

    def serialize(self):
        dt = pack("!Iff", int(self.tid), float(self.speedIn), float(self.speedOut))
        return dt

    # Да, если все значения нулевые
    def is_empty(self):
        return self.tid == 0 and self.speedIn == 0.001 and self.speedOut == 0.001

    def deserialize(self, data, *args):
        dt = unpack("!Iff", data)
        self.tid = int(dt[0])
        self.speedIn = float(dt[1])
        self.speedOut = float(dt[2])
        return self

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


# Абонент из базы
class AbonStruct(BaseStruct):
    def __init__(self, uid=0, ip=None, tariff=None, is_active=True):
        self.uid = int(uid or 0)
        self.ip = IpStruct(ip)
        self.tariff = tariff
        self.is_active = is_active

    def serialize(self):
        if self.tariff is None:
            return
        if not isinstance(self.tariff, TariffStruct):
            raise TypeError('Instance must be TariffStruct')
        if not isinstance(self.ip, IpStruct):
            raise TypeError('Instance must be IpStruct')
        dt = pack("!LII?", self.uid, int(self.ip), self.tariff.tid, self.is_active)
        return dt

    def deserialize(self, data, tariff=None):
        dt = unpack("!LII?", data)
        self.uid = dt[0]
        self.ip = IpStruct(dt[1])
        if tariff is not None:
            if not isinstance(tariff, TariffStruct):
                raise TypeError
            self.tariff = tariff
        self.is_active = dt['3']
        return self

    def __eq__(self, other):
        if not isinstance(other, AbonStruct):
            raise TypeError
        r = self.uid == other.uid and self.ip == other.ip
        r = r and self.tariff == other.tariff
        return r

    def __str__(self):
        return "uid=%d, ip=%s, tariff=%s" % (self.uid, self.ip, self.tariff or '<No Service>')

    def __hash__(self):
        return hash(int(self.ip) + hash(self.tariff)) if self.tariff is not None else 0


# Правило шейпинга в фаере, или ещё можно сказать услуга абонента на NAS
class ShapeItem(BaseStruct):
    def __init__(self, abon, sid):
        self.abon = abon
        self.sid = sid

    def serialize(self):
        abon_pack = self.abon.serialize()
        dt = pack('!L', self.sid)
        return dt + abon_pack

    def deserialize(self, data, *args):
        sz = calcsize('!L')
        dt = unpack('!L', data[:sz])
        self.sid = dt
        self.abon.deserialize(data[sz:])
        return self

    def __eq__(self, other):
        if not isinstance(other, ShapeItem):
            raise TypeError
        return self.sid == other.sid and self.abon == other.abon


VectorAbon = Iterable[AbonStruct]
VectorTariff = Iterable[TariffStruct]
