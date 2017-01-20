# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from netsnmp import Session, VarList, Varbind


class DevBase(object, metaclass=ABCMeta):
    @staticmethod
    def description():
        """Возвращает текстовое описание"""

    @abstractmethod
    def reboot(self):
        """Перезагружает устройство"""

    @abstractmethod
    def get_ports(self):
        """Получаем инфу о портах"""

    @abstractmethod
    def get_device_name(self):
        """Получаем имя устройства по snmp"""

    @abstractmethod
    def uptime(self):
        pass


class BasePort(object, metaclass=ABCMeta):
    def __init__(self, num, name, status, mac, speed):
        self.num = int(num)
        self.nm = name
        self.st = status
        self._mac = mac
        self.sp = speed

    @abstractmethod
    def disable(self):
        pass

    @abstractmethod
    def enable(self):
        pass

    def mac(self):
        m = self._mac
        return "%x:%x:%x:%x:%x:%x" % (ord(m[0]), ord(m[1]), ord(m[2]), ord(m[3]), ord(m[4]), ord(m[5]))


class SNMPBaseWorker(object, metaclass=ABCMeta):
    ses = None

    def __init__(self, ip, community='public', ver=2):
        self.ses = Session(DestHost=ip, Version=ver, Community=community)

    def set_int_value(self, oid, value):
        vs = VarList(Varbind(
            tag=oid,
            val=int(value),
            type='INTEGER'
        ))
        return self.ses.set(vs)

    def get_list(self, oid):
        vs = VarList(Varbind(oid))
        return self.ses.walk(vs)

    def get_item(self, oid):
        var = VarList(Varbind(oid))
        return self.ses.get(var)[0]
