from abc import ABCMeta, abstractmethod
from datetime import timedelta
from django.utils.translation import gettext
from typing import Union, Iterable, AnyStr, Generator, Optional

from easysnmp import Session

ListOrError = Union[
    Iterable,
    Union[Exception, Iterable]
]


class DeviceImplementationError(Exception):
    pass


class DevBase(object, metaclass=ABCMeta):
    def __init__(self, dev_instance=None):
        self.db_instance = dev_instance

    @staticmethod
    def description() -> AnyStr:
        pass

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def get_ports(self) -> ListOrError:
        pass

    @abstractmethod
    def get_device_name(self) -> AnyStr:
        """Return device name by snmp"""

    @abstractmethod
    def uptime(self) -> timedelta:
        pass

    @abstractmethod
    def get_template_name(self) -> AnyStr:
        """Return path to html template for device"""

    @staticmethod
    @abstractmethod
    def has_attachable_to_subscriber() -> bool:
        """Can connect device to subscriber"""

    @staticmethod
    @abstractmethod
    def is_use_device_port() -> bool:
        """True if used device port while opt82 authorization"""


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

    def mac(self) -> str:
        return ':'.join('%x' % ord(i) for i in self._mac)


class SNMPBaseWorker(object, metaclass=ABCMeta):
    ses = None

    def __init__(self, ip: Optional[str], community='public', ver=2):
        if ip is None or ip == '':
            raise DeviceImplementationError(gettext('Ip address is required'))
        self.ses = Session(hostname=ip, community=community, version=ver)

    def set_int_value(self, oid: str, value):
        return self.ses.set(oid, value, 'i')

    def get_list(self, oid) -> Generator:
        for v in self.ses.walk(oid):
            yield v.value

    def get_list_keyval(self, oid) -> Generator:
        for v in self.ses.walk(oid):
            snmpnum = v.oid.split('.')[-1:]
            yield v.value, snmpnum[0] if len(snmpnum) > 0 else None

    def get_item(self, oid):
        return self.ses.get(oid).value
