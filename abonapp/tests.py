# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.test import TestCase

from models import Abon, AbonTariff
from tariff_app.models import Tariff


class AbonTariffTestCase(TestCase):

    def setUp(self):
        abon1 = Abon.objects.create(
            telephone='+79784653751',
            fio=u'ФИО абона',
            username='аго мучич'
        )
        tarif1 = Tariff.objects.create(
            title=u'Тариф 1',
            speedIn=120.3,
            speedOut=53,
            amount=38
        )
        tarif2 = Tariff.objects.create(
            title=u'Тариф 2',
            speedIn=130.3,
            speedOut=23,
            amount=82
        )
        AbonTariff.objects.create(
            abon=abon1,
            tariff=tarif1,
            tariff_priority=0
        )
        AbonTariff.objects.create(
            abon=abon1,
            tariff=tarif2,
            tariff_priority=1
        )

    def test_activate_next(self):
        # возьмём абонента для опытов
        abn = get_object_or_404(Abon, username=u'аго мучич')

        # берём купленные услуги
        ats = AbonTariff.objects.filter(abon=abn)
        for at in ats:

            # и пробуем назначить
            at.activate_next_tariff()

        AbonTariff.objects.update_priorities(ats)
