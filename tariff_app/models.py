# -*- coding: utf-8 -*-
from django.db import models

from .custom_tariffs import TariffBase, TARIFF_CHOICES
from mydefs import MyChoicesAdapter


class Tariff(models.Model):
    title = models.CharField(max_length=32)
    descr = models.CharField(max_length=256)
    speedIn = models.FloatField(default=0.0)
    speedOut = models.FloatField(default=0.0)
    amount = models.FloatField(default=0.0)
    calc_type = models.CharField(max_length=2, default=TARIFF_CHOICES[0][0], choices=MyChoicesAdapter(TARIFF_CHOICES))
    is_admin = models.BooleanField(default=False)

    # Возвращает потомок класса TariffBase, методы которого дают нужную логику оплаты по тарифу
    def get_calc_type(self):
        ob = [TC for TC in TARIFF_CHOICES if TC[0] == self.calc_type]
        if len(ob) > 0:
            res_type = ob[0][1]
            assert issubclass(res_type, TariffBase)
            return res_type

    def calc_deadline(self):
        calc_type = self.get_calc_type()
        calc_obj = calc_type(self)
        return calc_obj.calc_deadline()

    def __str__(self):
        return "%s (%.2f)" % (self.title, self.amount)
