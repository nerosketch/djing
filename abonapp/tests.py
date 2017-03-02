from django.test import TestCase
from django.test.client import Client
from agent import NasNetworkError
from .models import AbonTariff, Abon
from tariff_app.models import Tariff


class AbonTestCase(TestCase):
    def setUp(self):
        try:
            Tariff.objects.create(
                title='test_tariff',
                descr='taroff descr',
                speedIn=1.2,
                speedOut=3.0,
                amount=3
            )
            Abon.objects.create(
                username='mainuser',
                telephone='+79788328884'
            )
        except NasNetworkError:
            pass

    # проверка на пополнение счёта
    def test_add_ballance(self):
        try:
            abon = Abon.objects.get(username='mainuser')
            ballance = abon.ballance
            abon.add_ballance(abon, 13, 'test pay')
            abon.save(update_fields=['ballance'])
            self.assertEqual(abon.ballance, ballance+13)
            ballance = abon.ballance
            abon.add_ballance(abon, 5.34, 'test float pay')
            abon.save(update_fields=['ballance'])
            self.assertEqual(abon.ballance, ballance+5.34)
        except NasNetworkError:
            pass

    # пробуем выбрать услугу
    def test_pick_tariff(self):
        try:
            tariff = Tariff.objects.get(title='test_tariff')
            abon = Abon.objects.get(username='mainuser')
            abon.pick_tariff(tariff, abon)
            act_tar = abon.active_tariff()

            # если недостаточно денег на счету
            assert abon.ballance <= tariff.amount
            # У абонента на счету 0, не должна быть куплена услуга
            self.assertEqual(act_tar, None)
            # Раз услуги нет то и доступа быть не должно
            self.assertTrue(not abon.is_access())

            # с деньгами
            abon.add_ballance(abon, 7.34, 'add pay for test pick tariff')
            abon.pick_tariff(tariff, abon)
            # должны получить указанную услугу
            self.assertEqual(act_tar, tariff)
            # и получить доступ
            self.assertTrue(abon.is_access())
        except NasNetworkError:
            pass



class AbonTariffTestCase(TestCase):
    def setUp(self):
        abon = Abon.objects.create(
            username='mainuser',
            telephone='+79788328884'
        )
        tariff = Tariff.objects.create(
            title='test_tariff',
            descr='taroff descr',
            speedIn=1.2,
            speedOut=3.0,
            amount=3
        )
        AbonTariff.objects.create(
            abon=abon,
            tariff=tariff
        )
