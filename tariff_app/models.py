# -*- coding: utf-8 -*-
from django.db import models
from custom_tariffs import TariffBase, TARIFF_CHOICES
from mydefs import MyChoicesAdapter
from agent import get_TransmitterClientKlass


# Класс похож на адаптер. Предназначен для Django CHOICES чтоб можно было передавать классывместо просто описания поля,
# классы передавать для того чтоб по значению из базы понять какой класс нужно взять для расчёта стоимости тарифа.
class _TariffChoicesAdapter(MyChoicesAdapter):

    # На вход принимает кортеж кортежей, вложенный из 2х элементов: кода и класса, как: TARIFF_CHOICES
    def __init__(self):
        super(_TariffChoicesAdapter, self).__init__(TARIFF_CHOICES)


class Tariff(models.Model):
    title = models.CharField(max_length=32)
    descr = models.CharField(max_length=256)
    speedIn = models.FloatField(default=0.0)
    speedOut = models.FloatField(default=0.0)
    amount = models.FloatField(default=0.0)
    time_of_action = models.IntegerField(default=30)
    calc_type = models.CharField(max_length=2, default=TARIFF_CHOICES[0][0], choices=_TariffChoicesAdapter())

    # Возвращает потомок класса TariffBase, методы которого дают нужную логику оплаты по тарифу
    def get_calc_type(self):
        ob = filter(lambda TC: TC[0] == self.calc_type, TARIFF_CHOICES)
        if len(ob) > 0:
            res_type = ob[0][1]
            assert issubclass(res_type, TariffBase)
            return res_type()

    def __unicode__(self):
        return u"%s (%f)" % (self.title, self.amount)


def tariff_save_signal(sender, instance, **kwargs):
    assert isinstance(instance, Tariff)
    tc = get_TransmitterClientKlass()()
    if kwargs['created']:
        tc.signal_tariff_create(instance)
    else:
        tc.signal_tariff_refresh(instance)


def tariff_remove_signal(sender, instance, **kwargs):
    assert isinstance(instance, Tariff)
    tc = get_TransmitterClientKlass()()
    tc.signal_tariff_remove(instance)


models.signals.pre_save.connect(tariff_save_signal, sender=Tariff)
models.signals.post_delete.connect(tariff_remove_signal, sender=Tariff)
