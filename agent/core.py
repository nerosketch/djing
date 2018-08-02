from abc import ABC, abstractmethod
from typing import Iterator, Any, Tuple, Optional

from .structs import AbonStruct, TariffStruct, VectorAbon, VectorTariff, IpStruct


# Raised if NAS has returned failed result
class NasFailedResult(Exception):
    pass


# Raised when is no connection to the NAS
class NasNetworkError(Exception):
    pass


# Communicate with NAS
class BaseTransmitter(ABC):
    @abstractmethod
    def add_user_range(self, user_list: VectorAbon):
        """add subscribers list to NAS"""

    @abstractmethod
    def remove_user_range(self, users: VectorAbon):
        """remove subscribers list"""

    @abstractmethod
    def add_user(self, user: AbonStruct, *args):
        """add subscriber"""

    @abstractmethod
    def remove_user(self, user: AbonStruct):
        """remove subscriber"""

    @abstractmethod
    def update_user(self, user: AbonStruct, *args):
        """
        Update subscriber by uid, you can change everything except its uid.
        Subscriber will found by UID.
        """

    @abstractmethod
    def add_tariff_range(self, tariff_list: VectorTariff):
        """Add services list to NAS."""

    @abstractmethod
    def remove_tariff_range(self, tariff_list: VectorTariff):
        """Remove tariff list by unique id list."""

    @abstractmethod
    def add_tariff(self, tariff: TariffStruct):
        pass

    @abstractmethod
    def update_tariff(self, tariff: TariffStruct):
        """
        Update tariff by uid, you can change everything except its uid.
        Tariff will found by UID.
        """

    @abstractmethod
    def remove_tariff(self, tid: int):
        """
        :param tid: unique id of tariff.
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
    def read_users(self) -> VectorAbon:
        pass

    @abstractmethod
    def lease_free(self, user: AbonStruct, lease: IpStruct):
        """
        Remove ip lease from allowed to network
        :return:
        """

    @abstractmethod
    def lease_start(self, user: AbonStruct, lease: IpStruct):
        """
        Starts ip lease to allowed to network
        :return:
        """

    def _diff_users(self, users_from_db: Iterator[Any]) -> Tuple[set, set]:
        """
        :param users_from_db: QuerySet of all subscribers that can have service
        :return: Tuple of 2 lists that contain list to add users and list to remove users
        """
        users_struct_list = (ab.build_agent_struct() for ab in users_from_db if ab.is_access())
        users_struct_set = set(ab for ab in users_struct_list if ab is not None and ab.tariff is not None)
        users_from_nas = set(self.read_users())
        if len(users_from_nas) < 1:
            print('WARNING: Not have users from NAS')
        list_for_del = (users_struct_set ^ users_from_nas) - users_struct_set
        list_for_add = users_struct_set - users_from_nas
        return list_for_add, list_for_del

    def sync_nas(self, users_from_db: Iterator):
        list_for_add, list_for_del = self._diff_users(users_from_db)
        if len(list_for_del) > 0:
            self.remove_user_range(list_for_del)
        if len(list_for_add) > 0:
            self.add_user_range(list_for_add)
