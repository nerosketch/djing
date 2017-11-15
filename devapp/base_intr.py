# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from easysnmp import Session


class DevBase(object, metaclass=ABCMeta):

    def __init__(self, dev_instance=None):
        self.db_instance = dev_instance

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

    @abstractmethod
    def get_template_name(self):
        """Получаем путь к html шаблону отображения устройства"""

    @staticmethod
    @abstractmethod
    def has_attachable_to_subscriber():
        """Можно-ли подключать устройство к абоненту"""

    @staticmethod
    @abstractmethod
    def is_use_device_port():
        """True если при авторизации по opt82 используется порт"""


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
        return ':'.join(['%x' % ord(i) for i in self._mac])


class SNMPBaseWorker(object, metaclass=ABCMeta):
    ses = None

    def __init__(self, ip, community='public', ver=2):
        self.ses = Session(hostname=ip, community=community, version=ver)

    def set_int_value(self, oid, value):
        return self.ses.set(oid, value)

    def get_list(self, oid):
        return self.ses.walk(oid)

    def get_list_keyval(self, oid):
        for v in self.ses.walk(oid):
            snmpnum = v.oid.split('.')[-1:]
            yield v.value, snmpnum[0] if len(snmpnum) > 0 else None

    def get_item(self, oid):
        return self.ses.get(oid).value
