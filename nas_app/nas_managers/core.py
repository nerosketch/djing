from abc import ABC, abstractmethod, abstractproperty
from typing import Iterator, Any, Tuple, Optional
from djing import ping
from nas_app.nas_managers.structs import SubnetQueue, VectorQueue


# Raised if NAS has returned failed result
class NasFailedResult(Exception):
    pass


# Raised when is no connection to the NAS
class NasNetworkError(Exception):
    pass


# Communicate with NAS
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
        """add subscribers list to NAS
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

    def _diff_users(self, users_from_db: Iterator[Any]) -> Tuple[set, set]:
        """
        :param users_from_db: QuerySet of all subscribers that can have service
        :return: Tuple of 2 lists that contain list to add users and list to remove users
        """
        users_struct_gen = (ab.build_agent_struct() for ab in users_from_db if
                            ab is not None and ab.is_access())
        users_struct_set = set(ab for ab in users_struct_gen if ab is not None and ab.tariff is not None)
        users_from_nas = set(self.read_users())
        if len(users_from_nas) < 1:
            print('WARNING: Not have users from NAS')
        list_for_del = (users_struct_set ^ users_from_nas) - users_struct_set
        list_for_add = users_struct_set - users_from_nas
        return list_for_add, list_for_del

    def sync_nas(self, users_from_db: Iterator):
        list_for_add, list_for_del = self._diff_users(users_from_db)
        if len(list_for_del) > 0:
            print('List for del:', len(list_for_del))
            for ld in list_for_del:
                print('\t', ld)
            self.remove_user_range(list_for_del)
        if len(list_for_add) > 0:
            print('List for add:', len(list_for_add))
            for la in list_for_add:
                print('\t', la)
            self.add_user_range(list_for_add)


def diff_set(one: set, two: set) -> Tuple[set, set]:
    list_for_del = (one ^ two) - one
    list_for_add = one - two
    return list_for_add, list_for_del
