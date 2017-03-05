# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from .structs import AbonStruct, TariffStruct


# Всплывает если из NAS вернулся не удачный результат
class NasFailedResult(Exception):
    pass


# Всплывает когда нет связи с сервером доступа к инету (NAS)
class NasNetworkError(Exception):
    pass


# Проверяет входной тип на принадлежность классу.
# Можно передать объект или коллекцию объектов
# В общем желание организовать строгую типизацию :)
def check_input_type(class_or_type):
    def real_check(fn):
        def wrapped(self, user):
            try:
                for usr in user:
                    assert isinstance(usr, class_or_type)
            except TypeError:
                assert isinstance(user, class_or_type)
            return fn(self, user)
        return wrapped
    return real_check


# Общается с NAS'ом
class BaseTransmitter(metaclass=ABCMeta):
    @abstractmethod
    @check_input_type(AbonStruct)
    def add_user_range(self, user_list):
        """добавляем список абонентов в NAS"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def remove_user_range(self, users):
        """удаляем список абонентов"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def add_user(self, user):
        """добавляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def remove_user(self, user):
        """удаляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def update_user(self, user):
        """чтоб обновить абонента можно изменить всё кроме его uid, по uid абонент будет найден"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def pause_user(self, user):
        """Приостановить обслуживание абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def start_user(self, user):
        """Продолжить обслуживание абонента"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff_range(self, tariff_list):
        """добавляем список тарифов в NAS"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff_range(self, tariff_list):
        """удаляем список тарифов по уникальным идентификаторам"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff(self, tariff):
        """добавляем тариф"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def update_tariff(self, tariff):
        """чтоб обновить тариф надо изменить всё кроме его tid, по tid тариф будет найден"""

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff(self, tid):
        """удаляем тариф"""
