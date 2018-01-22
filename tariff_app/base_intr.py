# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod


class TariffBase(metaclass=ABCMeta):
    @abstractmethod
    def calc_amount(self):
        """Calculates total amount of payment"""
        raise NotImplementedError

    @abstractmethod
    def calc_deadline(self):
        """Calculate deadline date"""
        raise NotImplementedError

    @staticmethod
    def description():
        """
        Usage in mydefs.MyChoicesAdapter for choices fields.
        :return: human readable description
        """
        raise NotImplementedError

    @staticmethod
    def manage_access(abon):
        """Manage subscribers access to service"""
        #assert isinstance(abon, Abon)
        if not abon.is_active: return False
        act_tar = abon.active_tariff()
        if act_tar:
            return True


class PeriodicPayCalcBase(metaclass=ABCMeta):

    @abstractmethod
    def calc_amount(self, model_object):
        """
        :param model_object: it is a instance of models.PeriodicPay model
        :return: float: amount for the service
        """
        raise NotImplementedError

    @abstractmethod
    def get_next_time_to_pay(self, model_object, last_time_payment):
        """
        :param model_object: it is a instance of models.PeriodicPay model
        :param last_time_payment: May be None if first pay
        :return: datetime.datetime: time for next pay
        """
        raise NotImplementedError

    @staticmethod
    def description():
        """Return text description.
        Uses in mydefs.MyChoicesAdapter for CHOICES fields"""
        raise NotImplementedError
