from abc import ABCMeta
from ipaddress import ip_address, _BaseAddress
from typing import Iterable


class BaseStruct(object, metaclass=ABCMeta):

    def __ne__(self, other):
        return not self == other


class TariffStruct(BaseStruct):
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
    __slots__ = ('ip', 'uid', 'tariff', 'is_active', 'queue_id')

    def __init__(self, uid=0, ip=None, tariff=None, is_active=True):
        self.uid = int(uid or 0)
        if issubclass(ip.__class__, _BaseAddress):
            self.ip = ip
        else:
            self.ip = ip_address(ip)
        self.tariff = tariff
        self.is_active = is_active

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


# Shape rule from NAS(Network Access Server)
class ShapeItem(BaseStruct):
    def __init__(self, abon, sid):
        self.abon = abon
        self.sid = sid

    def __eq__(self, other):
        if not isinstance(other, ShapeItem):
            raise TypeError
        return self.sid == other.sid and self.abon == other.abon


VectorAbon = Iterable[AbonStruct]
VectorTariff = Iterable[TariffStruct]
