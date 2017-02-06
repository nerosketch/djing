# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils import timezone
from .base_intr import TariffBase

# from abonapp import AbonTariff


class TariffDefault(TariffBase):
    # Базовый функционал считает стоимость пропорционально использованному времени
    def calc_amount(self, abon_tariff):
        #assert isinstance(abon_tariff, AbonTariff)
        # сейчас
        nw = timezone.now()

        # сколько прошло с начала действия услуги
        # если времени начала нет то это начало действия, использованное время 0
        time_diff = nw - abon_tariff.time_start if abon_tariff.time_start else timedelta(0)

        # времени в этом месяце
        curr_month_time = datetime(nw.year, nw.month if nw.month == 12 else nw.month + 1, 1) - timedelta(days=1)
        curr_month_time = timedelta(days=curr_month_time.day)

        # Сколько это в процентах от всего месяца (k - коеффициент)
        k = time_diff.total_seconds() / curr_month_time.total_seconds()

        # результат - это полная стоимость тарифа умноженная на k
        res = k * abon_tariff.tariff.amount

        return float(res)

    # возвращаем сколько времени осталось до завершения услуги (конца месяца)
    def get_avail_time(self):
        from calendar import monthrange
        nw = timezone.now()
        last_day = monthrange(nw.year, nw.month)[1]
        last_month_date = datetime(year=nw.year, month=nw.month, day=last_day,
                                   hour=23,minute=59, second=59,tzinfo=nw.tzinfo)
        return last_month_date - nw

    @staticmethod
    def description():
        return 'Базовый расчётный функционал'


class TariffDp(TariffDefault):
    # в IS снимается вся стоимость тарифа вне зависимости от времени использования

    # просто возвращаем всю стоимость тарифа
    def calc_amount(self, abon_tariff):
        return float(abon_tariff.tariff.amount)

    @staticmethod
    def description():
        return 'Как в IS'


class TariffCp(TariffDefault):
    def calc_amount(self, abon_tariff):
        return 12.6

    @staticmethod
    def description():
        return 'Пользовательский'


# Первый - всегда по умолчанию
TARIFF_CHOICES = (
    ('Df', TariffDefault),
    ('Dp', TariffDp),
    ('Cp', TariffCp)
)
