from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import AnyStr, Optional, Union


class TariffBase(metaclass=ABCMeta):
    @abstractmethod
    def calc_amount(self) -> float:
        """Calculates total amount of payment"""
        raise NotImplementedError

    @abstractmethod
    def calc_deadline(self) -> datetime:
        """Calculate deadline date"""
        raise NotImplementedError

    @staticmethod
    def description() -> AnyStr:
        """
        Usage in djing.lib.MyChoicesAdapter for choices fields.
        :return: human readable description
        """
        raise NotImplementedError

    @staticmethod
    def manage_access(abon) -> bool:
        """Manage subscribers access to service"""
        if not abon.is_active:
            return False
        act_tar = abon.active_tariff()
        if act_tar:
            return True
        return False


class PeriodicPayCalcBase(metaclass=ABCMeta):
    @abstractmethod
    def calc_amount(self, model_object) -> float:
        """
        :param model_object: it is a instance of models.PeriodicPay model
        :return: float: amount for the service
        """
        raise NotImplementedError

    @abstractmethod
    def get_next_time_to_pay(self, model_object, last_time_payment: Optional[Union[datetime, None]]) -> datetime:
        """
        :param model_object: it is a instance of models.PeriodicPay model
        :param last_time_payment: May be None if first pay
        :return: datetime.datetime: time for next pay
        """
        raise NotImplementedError

    @staticmethod
    def description() -> AnyStr:
        """Return text description.
        Uses in djing.lib.MyChoicesAdapter for CHOICES fields"""
        raise NotImplementedError
