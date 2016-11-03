# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.utils import timezone

from base_intr import TariffBase

#from abonapp import AbonTariff


class TariffDefault(TariffBase):

    # Базовый функционал считает стоимость пропорционально использованному времени
    def calc_amount(self, abon_tariff):
        #assert isinstance(abon_tariff, AbonTariff)
        # сейчас
        nw = datetime.now(tz=timezone.get_current_timezone())

        # сколько прошло с начала действия услуги
        time_diff = nw - abon_tariff.time_start

        # времени в этом месяце
        curr_month_time = datetime(nw.year, nw.month+1, 1) - timedelta(days = 1)
        curr_month_time = timedelta(days=curr_month_time.day)

        # Сколько это в процентах от всего месяца (k - коеффициент, т.е. без %)
        k = time_diff.total_seconds() / curr_month_time.total_seconds()

        # результат - это полная стоимость тарифа умноженная на k
        res = k * abon_tariff.tariff.amount

        return float(res)

    @staticmethod
    def description():
        return u'Базовый расчётный функционал'


class TariffDp(TariffBase):
    # в IS снимается вся стоимость тарифа вне зависимости от времени использования

    # просто возвращаем всю стоимость тарифа
    def calc_amount(self, abon_tariff):
        return float(abon_tariff.tariff.amount)

    @staticmethod
    def description():
        return u'Как в IS'


class TariffCp(TariffBase):

    def calc_amount(self, abon_tariff):
        return 12.6

    @staticmethod
    def description():
        return u'Пользовательский'


# Первый - всегда по умолчанию
TARIFF_CHOICES = (
    ('Df', TariffDefault),
    ('Dp', TariffDp),
    ('Cp', TariffCp)
)
