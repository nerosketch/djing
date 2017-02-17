# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from struct import pack, unpack, calcsize
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

    def get_str(self):
        return int2ip(self.__ip)

    def get_int(self):
        return self.__ip

    def __eq__(self, other):
        assert isinstance(other, IpStruct)
        return self.__ip == other.__ip

    def __str__(self):
        return int2ip(self.__ip)


# Как обслуживается абонент
class TariffStruct(BaseStruct):

    def __init__(self, tariff_id=0, speedIn=None, speedOut=None):
        self.tid = tariff_id
        self.speedIn = float(speedIn or 0.0625)
        self.speedOut = float(speedOut or 0.0625)

    def serialize(self):
        dt = pack("!Iff", int(self.tid), float(self.speedIn), float(self.speedOut))
        return dt

    def deserialize(self, data, *args):
        dt = unpack("!Iff", data)
        self.tid = int(dt[0])
        self.speedIn = float(dt[1])
        self.speedOut = float(dt[2])
        return self

    def __eq__(self, other):
        assert isinstance(other, TariffStruct)
        # не сравниваем id, т.к. тарифы с одинаковыми скоростями для NAS одинаковы
        # Да и иногда не удобно доставать из nas id тарифы из базы
        return self.speedIn == other.speedIn and self.speedOut == other.speedOut

    def __str__(self):
        return "Id=%d, speedIn=%.2f, speedOut=%.2f" % (self.tid, self.speedIn, self.speedOut)


# Абонент из базы
class AbonStruct(BaseStruct):

    def __init__(self, uid=None, ip=None, tariff=None):
        self.uid = int(uid)
        self.ip = IpStruct(ip)
        assert isinstance(tariff, TariffStruct)
        self.tariff = tariff

    def serialize(self):
        assert isinstance(self.tariff, TariffStruct)
        assert isinstance(self.ip, IpStruct)
        dt = pack("!LII", self.uid, self.ip.get_int(), self.tariff.tid)
        return dt

    def deserialize(self, data, tariff=None):
        dt = unpack("!LII", data)
        self.uid = dt[0]
        self.ip = IpStruct(dt[1])
        if tariff is not None:
            assert isinstance(tariff, TariffStruct)
            self.tariff = tariff
        return self

    def __eq__(self, other):
        assert isinstance(other, AbonStruct)
        r = self.uid == other.uid and self.ip == other.ip
        r = r and self.tariff == other.tariff
        return r

    def __str__(self):
        return "uid=%d, ip=%s, tariff=%s" % (self.uid, self.ip, self.tariff)


# Правило шейпинга в фаере, или ещё можно сказать услуга абонента на NAS
class ShapeItem(BaseStruct):
    def __init__(self, abon, sid):
        self.abon = abon
        self.sid = sid

    def serialize(self):
        abon_pack = self.abon.serialize()
        dt = pack('!L', self.sid)
        return dt+abon_pack

    def deserialize(self, data, *args):
        sz = calcsize('!L')
        dt = unpack('!L', data[:sz])
        self.sid = dt
        self.abon.deserialize(data[sz:])
        return self

    def __eq__(self, other):
        assert isinstance(other, ShapeItem)
        return self.sid == other.sid and self.abon == other.abon
