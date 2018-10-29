from abc import ABC, abstractmethod, abstractproperty
from typing import Iterator, Tuple, Optional
from djing import ping
from gw_app.nas_managers.structs import SubnetQueue, VectorQueue


# Raised if gw has returned failed result
class NasFailedResult(Exception):
    pass


# Raised when is no connection to the gw
class NasNetworkError(Exception):
    pass


# Communicate with gw
class BaseTransmitter(ABC):
    @abstractproperty
    def description(self):
        """
        :return: Returnd a description of nas implementation
        """

    def __init__(self, ip: str, *args, **kwargs):
        if not ping(ip):
            raise NasNetworkError('NAS %(ip_addr)s does not pinged' % {
                'ip_addr': ip
            })

    @classmethod
    def get_description(cls):
        return cls.description

    @abstractmethod
    def add_user_range(self, queue_list: VectorQueue):
        """add subscribers list to gateway
        :param queue_list: Vector of instances of subscribers
        """

    @abstractmethod
    def remove_user_range(self, queues):
        """remove subscribers list
        :param queues: Vector of instances of subscribers
        """

    @abstractmethod
    def add_user(self, queue: SubnetQueue, *args):
        """add subscriber
        :param queue: Subscriber instance
        """

    @abstractmethod
    def remove_user(self, queue: SubnetQueue):
        """
        remove subscriber
        :param queue: Subscriber instance
        """

    @abstractmethod
    def update_user(self, queue: SubnetQueue, *args):
        """
        Update subscriber by uid, you can change everything except its uid.
        Subscriber will found by UID.
        :param queue: Subscriber instance
        """

    @abstractmethod
    def ping(self, host: str, count=10) -> Optional[Tuple[int, int]]:
        """
        :param host: ip address in text view, for example '192.168.0.1'
        :param count: count of ping queries
        :return: None if not response, else tuple it contains count returned and count sent
        for example (received, sent) -> (7, 10).
        """

    @abstractmethod
    def read_users(self) -> VectorQueue:
        pass

    @abstractmethod
    def sync_nas(self, users_from_db: Iterator):
        """
        Synchronize db with gateway
        :param users_from_db: Queryset of allowed users
        :return: nothing
        """


def diff_set(one: set, two: set) -> Tuple[set, set]:
    list_for_del = (one ^ two) - one
    list_for_add = one - two
    return list_for_add, list_for_del
