# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from typing import AnyStr

from django.utils import timezone
from django.utils.translation import gettext as _
from .base_intr import TariffBase, PeriodicPayCalcBase
from calendar import monthrange

from random import uniform


class TariffDefault(TariffBase):
    def __init__(self, abon_tariff):
        # assert isinstance(abon_tariff, AbonTariff)
        self.abon_tariff = abon_tariff

    # Базовый функционал считает стоимость пропорционально использованному времени
    def calc_amount(self) -> float:
        # сейчас
        nw = timezone.now()

        # сколько прошло с начала действия услуги
        # если времени начала нет то это начало действия, использованное время 0
        time_diff = nw - self.abon_tariff.time_start if self.abon_tariff.time_start else timedelta(0)

        # времени в этом месяце
        curr_month_time = datetime(nw.year, nw.month if nw.month == 12 else nw.month + 1, 1) - timedelta(days=1)
        curr_month_time = timedelta(days=curr_month_time.day)

        # Сколько это в процентах от всего месяца (k - коеффициент)
        k = time_diff.total_seconds() / curr_month_time.total_seconds()

        # результат - это полная стоимость тарифа умноженная на k
        res = k * self.abon_tariff.tariff.amount

        return float(res)

    # Тут мы расчитываем конец действия услуги, завершение будет в конце месяца
    def calc_deadline(self) -> datetime:
        nw = timezone.now()
        last_day = monthrange(nw.year, nw.month)[1]
        last_month_date = datetime(year=nw.year, month=nw.month, day=last_day,
                                   hour=23, minute=59, second=59)
        return last_month_date

    @staticmethod
    def description() -> AnyStr:
        return _('Base calculate functionality')


class TariffDp(TariffDefault):
    # в IS снимается вся стоимость тарифа вне зависимости от времени использования

    # просто возвращаем всю стоимость тарифа
    def calc_amount(self) -> float:
        return float(self.abon_tariff.tariff.amount)

    @staticmethod
    def description() -> AnyStr:
        return 'IS'


# Как в IS только не на время, а на 10 лет
class TariffCp(TariffDp):
    def calc_deadline(self) -> datetime:
        # делаем время окончания услуги на 10 лет вперёд
        nw = timezone.now()
        long_long_time = datetime(year=nw.year + 10, month=nw.month, day=nw.day,
                                  hour=23, minute=59, second=59)
        return long_long_time

    @staticmethod
    def description() -> AnyStr:
        return _('Private service')


# Daily service
class TariffDaily(TariffDp):

    def calc_deadline(self):
        nw = timezone.now()
        # next day in the same time
        one_day = timedelta(days=1)
        return nw + one_day

    @staticmethod
    def description() -> AnyStr:
        return _('IS Daily service')


# Первый - всегда по умолчанию
TARIFF_CHOICES = (
    ('Df', TariffDefault),
    ('Dp', TariffDp),
    ('Cp', TariffCp),
    ('Dl', TariffDaily)
)


class PeriodicPayCalcDefault(PeriodicPayCalcBase):
    def calc_amount(self, model_object) -> float:
        return model_object.amount

    def get_next_time_to_pay(self, model_object, last_time_payment) -> datetime:
        # TODO: решить какой будет расёт периодических платежей
        return datetime.now() + timedelta(days=30)

    @staticmethod
    def description() -> AnyStr:
        return _('Default periodic pay')


class PeriodicPayCalcCustom(PeriodicPayCalcDefault):
    def calc_amount(self, model_object) -> float:
        """
        :param model_object: it is a instance of models.PeriodicPay model
        :return: float: amount for the service
        """
        return uniform(1, 10)

    @staticmethod
    def description() -> AnyStr:
        return _('Custom periodic pay')


PERIODIC_PAY_CHOICES = (
    ('df', PeriodicPayCalcDefault),
    ('cs', PeriodicPayCalcCustom)
)
