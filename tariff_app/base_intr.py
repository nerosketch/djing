# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod


class TariffBase(object):
    __metaclass__ = ABCMeta

    # Принимает на вход:
    # abon_tariff - models.AbonTariff object
    @abstractmethod
    def calc_amount(self, abon_tariff):
        """Считает итоговую сумму платежа"""

    @staticmethod
    def description():
        """Возвращает текстовое описание"""
