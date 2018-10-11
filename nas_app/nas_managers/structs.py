from abc import ABCMeta
from ipaddress import ip_address, _BaseAddress
from typing import Iterable


class BaseStruct(object, metaclass=ABCMeta):
    __slots__ = ()


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
    __slots__ = ('uid', '_ip', 'tariff', 'is_access', 'queue_id')

    def __init__(self, uid=0, ip=None, tariff=None, is_access=True):
        self.uid = int(uid or 0)
        self._ip = ip
        self.tariff = tariff
        self.is_access = is_access
        self.queue_id = 0

    def get_ip(self):
        return self._ip

    def set_ip(self, v):
        if issubclass(v.__class__, _BaseAddress):
            self._ip = v
        else:
            self._ip = ip_address(v)

    ip = property(get_ip, set_ip, doc='Ip address')

    def __eq__(self, other):
        if not isinstance(other, AbonStruct):
            raise TypeError
        r = self.uid == other.uid and self._ip == other._ip
        r = r and self.tariff == other.tariff
        return r

    def __str__(self):
        return "uid=%d, ip=[%s], tariff=%s" % (self.uid, self._ip, self.tariff or '<No Service>')

    def __hash__(self):
        return hash(hash(self._ip) + hash(self.tariff) if self.tariff is not None else 0)


VectorAbon = Iterable[AbonStruct]
VectorTariff = Iterable[TariffStruct]
