# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
# from abonapp import Abon


class TariffBase(metaclass=ABCMeta):
    @abstractmethod
    def calc_amount(self):
        """Считает итоговую сумму платежа"""

    @abstractmethod
    def calc_deadline(self):
        """Считаем дату, до которой действкет тариф"""

    @staticmethod
    def description():
        """Возвращает текстовое описание"""

    @staticmethod
    def manage_access(abon):
        """Управляет доступом абонента к услуге"""
        #assert isinstance(abon, Abon)
        # если абонент не активен то выходим
        if not abon.is_active: return False
        # смотрим на текущую услугу
        act_tar = abon.active_tariff()
        # если есть услуга
        if act_tar:
            return True
