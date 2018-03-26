# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from typing import Iterator, Any, Tuple

from .structs import AbonStruct, TariffStruct, VectorAbon, VectorTariff


# Всплывает если из NAS вернулся не удачный результат
class NasFailedResult(Exception):
    pass


# Всплывает когда нет связи с сервером доступа к инету (NAS)
class NasNetworkError(Exception):
    pass


# Общается с NAS'ом
class BaseTransmitter(metaclass=ABCMeta):
    @abstractmethod
    def add_user_range(self, user_list: VectorAbon):
        """добавляем список абонентов в NAS"""

    @abstractmethod
    def remove_user_range(self, users: VectorAbon):
        """удаляем список абонентов"""

    @abstractmethod
    def add_user(self, user: AbonStruct, *args):
        """добавляем абонента"""

    @abstractmethod
    def remove_user(self, user: AbonStruct):
        """удаляем абонента"""

    @abstractmethod
    def update_user(self, user: AbonStruct, *args):
        """чтоб обновить абонента можно изменить всё кроме его uid, по uid абонент будет найден"""

    @abstractmethod
    def add_tariff_range(self, tariff_list: VectorTariff):
        """
        Пока не используется, зарезервировано.
        Добавляет список тарифов в NAS
        """

    @abstractmethod
    def remove_tariff_range(self, tariff_list: VectorTariff):
        """
        Пока не используется, зарезервировано.
        Удаляем список тарифов по уникальным идентификаторам
        """

    @abstractmethod
    def add_tariff(self, tariff: TariffStruct):
        """
        Пока не используется, зарезервировано.
        Добавляет тариф
        """

    @abstractmethod
    def update_tariff(self, tariff: TariffStruct):
        """
        Пока не используется, зарезервировано.
        Чтоб обновить тариф надо изменить всё кроме его tid, по tid тариф будет найден
        """

    @abstractmethod
    def remove_tariff(self, tid: int):
        """
        :param tid: id тарифа в среде NAS сервера чтоб удалить по этому номеру
        Пока не используется, зарезервировано.
        """

    @abstractmethod
    def ping(self, host: str, count=10):
        """
        :param host: ip адрес в текстовом виде, например '192.168.0.1'
        :param count: количество пингов
        :return: None если не пингуется, иначе кортеж, в котором (сколько вернулось, сколько было отправлено)
        """

    @abstractmethod
    def read_users(self):
        """
        Читаем пользователей с NAS
        :return: список AbonStruct
        """

    def _diff_users(self, users_from_db: Iterator[Any]) -> Tuple[set, set]:
        """
        :param users_from_db: QuerySet всех абонентов у которых может быть обслуживание
        :return: на выходе получаем абонентов которых надо добавить в nas и которых надо удалить
        """
        users_struct_list = [ab.build_agent_struct() for ab in users_from_db if ab.is_access()]
        users_struct_set = set([ab for ab in users_struct_list if ab is not None and ab.tariff is not None])
        users_from_nas = set(self.read_users())
        list_for_del = (users_struct_set ^ users_from_nas) - users_struct_set
        list_for_add = users_struct_set - users_from_nas
        return list_for_add, list_for_del

    def sync_nas(self, users_from_db: Iterator):
        list_for_add, list_for_del = self._diff_users(users_from_db)
        if len(list_for_del) > 0:
            print('FOR DELETE')
            for ld in list_for_del:
                print(ld)
            self.remove_user_range(list_for_del)
        if len(list_for_add) > 0:
            print('FOR ADD')
            for la in list_for_add:
                print(la)
            self.add_user_range(list_for_add)
