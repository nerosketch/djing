from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Union, Iterable, AnyStr, Generator, Optional
from easysnmp import Session

from django.utils.translation import gettext

from djing.lib.decorators import abstract_static_method

ListOrError = Union[
    Iterable,
    Union[Exception, Iterable]
]


class DeviceImplementationError(Exception):
    pass


class DevBase(object, metaclass=ABCMeta):
    def __init__(self, dev_instance=None):
        self.db_instance = dev_instance

    @abstract_static_method
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

    @abstract_static_method
    def has_attachable_to_subscriber() -> bool:
        """Can connect device to subscriber"""

    @abstract_static_method
    def is_use_device_port() -> bool:
        """True if used device port while opt82 authorization"""

    @abstract_static_method
    def validate_extra_snmp_info(v: str) -> None:
        """
        Validate extra snmp field for each device.
        If validation failed then raise en exception from djing.lib.tln.ValidationError
        with description of error.
        :param v: String value for validate
        """

    @abstract_static_method
    def monitoring_template(device_instance, *args, **kwargs) -> Optional[str]:
        """
        Template for monitoring system config
        :return: string for config file
        """


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
        self._ip = ip
        self._community = community
        self._ver = ver

    def start_ses(self):
        if self.ses is None:
            self.ses = Session(hostname=self._ip, community=self._community, version=self._ver)

    def set_int_value(self, oid: str, value):
        self.start_ses()
        return self.ses.set(oid, value, 'i')

    def get_list(self, oid) -> Generator:
        self.start_ses()
        for v in self.ses.walk(oid):
            yield v.value

    def get_list_keyval(self, oid) -> Generator:
        self.start_ses()
        for v in self.ses.walk(oid):
            snmpnum = v.oid.split('.')[-1:]
            yield v.value, snmpnum[0] if len(snmpnum) > 0 else None

    def get_item(self, oid):
        self.start_ses()
        return self.ses.get(oid).value
