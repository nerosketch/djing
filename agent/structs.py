# -*- coding: utf8 -*-
from abc import ABCMeta, abstractmethod
from struct import pack, unpack
from utils import int2ip, ip2int


class BaseStruct(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialize(self):
        """привращаем инфу в бинарную строку"""

    @abstractmethod
    def deserialize(self, data, *args):
        """создаём объект из бинарной строки"""


class IpStruct(object):

    def __init__(self, ip):
        if type(ip) is int:
            self.__ip = ip
        else:
            self.__ip = ip2int(ip)

    def get_str(self):
        return int2ip(self.__ip)

    def get_int(self):
        return self.__ip


# Как обслуживается абонент
class TariffStruct(BaseStruct):

    def __init__(self, tariff_id=0, speedIn=None, speedOut=None):
        self.tid = tariff_id
        self.speedIn = speedIn
        self.speedOut = speedOut

    def serialize(self):
        dt = pack("!Iff", int(self.tid), float(self.speedIn), float(self.speedOut))
        return dt

    def deserialize(self, data, *args):
        dt = unpack("!Iff", data)
        self.tid = int(dt[0])
        self.speedIn = float(dt[1])
        self.speedOut = float(dt[2])
        return self


# Абонент из базы
class AbonStruct(BaseStruct):

    def __init__(self, uid=None, ip=None, tariff=None):
        self.uid = long(uid)
        self.ip = IpStruct(ip)
        assert isinstance(tariff, TariffStruct)
        self.tariff = tariff

    def serialize(self):
        assert isinstance(self.tariff, TariffStruct)
        assert isinstance(self.ip, IpStruct)
        dt = pack("!LII", self.uid, self.ip.get_int(), self.tariff.tid)
        return dt

    def deserialize(self, data, all_tarifs=None):
        dt = unpack("!LII", data)
        self.uid = dt[0]
        self.ip = IpStruct(dt[1])
        tarifs = filter(lambda trf: trf.tid == dt[2], all_tarifs)
        if len(tarifs) < 1:
            raise IndexError
        assert isinstance(tarifs[0], TariffStruct)
        self.tariff = tarifs[0]
        return self
