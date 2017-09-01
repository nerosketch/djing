# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from .structs import AbonStruct, TariffStruct


# Всплывает если из NAS вернулся не удачный результат
class NasFailedResult(Exception):
    pass


# Всплывает когда нет связи с сервером доступа к инету (NAS)
class NasNetworkError(Exception):
    pass


# Проверяет входной объект на принадлежность типу.
# Можно передать несколько типов в соответствии количеству параметров
# В общем желание организовать строгую типизацию :)
def check_input_type(*types):
    def real_check(fn):
        def wrapped(self, *args):
            if len(types) != len(args):
                raise AttributeError("length of @types must be equivalent for length of @args")
            for param_type, param in zip(types, args):
                if not isinstance(param, param_type):
                    raise TypeError("%s must be %s, but is %s" % (str(param), str(param_type), type(param)))
            return fn(self, *args)
        return wrapped
    return real_check


# Общается с NAS'ом
class BaseTransmitter(metaclass=ABCMeta):
    @abstractmethod
    @check_input_type(set)
    def add_user_range(self, user_list):
        """добавляем список абонентов в NAS"""

    @abstractmethod
    @check_input_type(set)
    def remove_user_range(self, users):
        """удаляем список абонентов"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def add_user(self, user, *args):
        """добавляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def remove_user(self, user):
        """удаляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def update_user(self, user, *args):
        """чтоб обновить абонента можно изменить всё кроме его uid, по uid абонент будет найден"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff_range(self, tariff_list):
        """
        Пока не используется, зарезервировано.
        Добавляет список тарифов в NAS
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff_range(self, tariff_list):
        """
        Пока не используется, зарезервировано.
        Удаляем список тарифов по уникальным идентификаторам
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff(self, tariff):
        """
        Пока не используется, зарезервировано.
        Добавляет тариф
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def update_tariff(self, tariff):
        """
        Пока не используется, зарезервировано.
        Чтоб обновить тариф надо изменить всё кроме его tid, по tid тариф будет найден
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff(self, tid):
        """
        :param tid: id тарифа в среде NAS сервера чтоб удалить по этому номеру
        Пока не используется, зарезервировано.
        """

    @abstractmethod
    @check_input_type(str)
    def ping(self, host, count=10):
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

    def _diff_users(self, users_from_db):
        """
        :param users_from_db: QuerySet всех абонентов у которых может быть обслуживание
        :return: на выходе получаем абонентов которых надо добавить в nas и которых надо удалить
        """
        users_from_db = [ab.build_agent_struct() for ab in users_from_db if ab.is_access()]
        users_from_db = set([ab for ab in users_from_db if ab is not None and ab.tariff is not None])
        users_from_nas = set(self.read_users())
        list_for_del = (users_from_db ^ users_from_nas) - users_from_db
        list_for_add = users_from_db - users_from_nas
        return list_for_add, list_for_del

    def sync_nas(self, users_from_db):
        list_for_add, list_for_del = self._diff_users(users_from_db)
        print('FOR DELETE')
        for ld in list_for_del:
            print(ld)
        print('FOR ADD')
        for la in list_for_add:
            print(la)
        self.remove_user_range( list_for_del )
        self.add_user_range( list_for_add )
