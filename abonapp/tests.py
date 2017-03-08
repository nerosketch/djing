from django.test import TestCase
from django.test.client import Client
from agent import NasNetworkError
from .models import AbonTariff, Abon, AbonGroup, LogicError, AbonRawPassword
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
            abon = Abon()
            abon.username = '1234567'
            abon.fio = 'mainuser'
            abon.telephone = '+79788328884'
            abon.set_password('ps')
            abon.is_superuser = True
            abon.save()
            abon_group = AbonGroup.objects.create(title='abon_group')
            abon_group.profiles.add(abon)
        except NasNetworkError:
            pass

    # проверка на пополнение счёта
    def test_add_ballance(self):
        try:
            abon = Abon.objects.get(username='1234567')
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
            abon = Abon.objects.get(username='1234567')
            try:
                abon.pick_tariff(tariff, abon)
                # нет денег, должно всплыть исключение и сюда дойти мы не должны
                self.assertFalse(True)
            except LogicError:
                pass
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
            act_tar = abon.active_tariff()
            # должны получить указанную услугу
            self.assertEqual(act_tar, tariff)
            # и получить доступ
            self.assertTrue(abon.is_access())
        except NasNetworkError:
            pass

    # тестим очередь услуг
    def test_services_queue(self):
        abon = Abon.objects.get(username='1234567')
        tariff = Tariff.objects.get(title='test_tariff')
        abon.add_ballance(abon, 9, 'add pay for test services queue')
        abon.save()
        abon.pick_tariff(tariff, abon)
        abon.pick_tariff(tariff, abon)
        abon.pick_tariff(tariff, abon)
        # снять деньги должно было только за первый выбор, остальные стают в очередь услуг
        self.assertEqual(abon.ballance, 6)

        c = Client()
        # login
        c.post('/accounts/login/', {'login': '1234567', 'password': 'ps'})
        resp = c.get('/abons/1/1/complete_service1')
        print('RESP:', resp)
        self.assertEqual(resp.status_code, 200)
        resp = c.post('/abons/1/1/complete_service1', data={
            'finish_confirm': 'yes'
        })
        print('RESP:', resp)
        # при успешной остановке услуги идёт редирект на др страницу
        self.assertEqual(resp.status_code, 302)
        # текущей услуги быть не должно
        act_tar = abon.active_tariff()
        self.assertIsNone(act_tar)
        # не активных услуг останется 2
        noact_count = AbonTariff.objects.filter(abon=abon).filter(time_start=None).count()
        self.assertEqual(noact_count, 2)

    # проверяем платёжку alltime
    def test_allpay(self):
        from hashlib import md5
        from djing.settings import pay_SECRET, pay_SERV_ID
        import xmltodict
        def sig(act, pay_account, pay_id):
            md = md5()
            s = '_'.join((str(act), str(pay_account), pay_SERV_ID, str(pay_id), pay_SECRET))
            md.update(bytes(s, 'utf-8'))
            return md.hexdigest()
        c = Client()
        r = c.get('/abons/pay', {
            'ACT': 1, 'PAY_ACCOUNT': '1234567',
            'SERVICE_ID': pay_SERV_ID,
            'PAY_ID': 3561234,
            'TRADE_POINT': 377,
            'SIGN': sig(1, 1234567, 3561234)
        })
        xobj = xmltodict.parse(r.content)
        self.assertEqual(int(xobj['pay-response']['status_code']), 21)
        r = c.get('/abons/pay', {
            'ACT': 4, 'PAY_ACCOUNT': '1234567',
            'SERVICE_ID': pay_SERV_ID,
            'PAY_ID': 3561234,
            'PAY_AMOUNT': 1.0,
            'TRADE_POINT': 377,
            'SIGN': sig(4, 1234567, 3561234)
        })
        xobj = xmltodict.parse(r.content)
        self.assertEqual(int(xobj['pay-response']['status_code']), 22)
        r = c.get('/abons/pay', {
            'ACT': 4, 'PAY_ACCOUNT': '1234567',
            'SERVICE_ID': pay_SERV_ID,
            'PAY_ID': 3561234,
            'PAY_AMOUNT': 1.0,
            'TRADE_POINT': 377,
            'SIGN': sig(4, 1234567, 3561234)
        })
        xobj = xmltodict.parse(r.content)
        self.assertEqual(int(xobj['pay-response']['status_code']), -100)
        r = c.get('/abons/pay', {
            'ACT': 7, 'PAY_ACCOUNT': '1234567',
            'SERVICE_ID': pay_SERV_ID,
            'PAY_ID': 3561234,
            'PAY_AMOUNT': 1.0,
            'TRADE_POINT': 377,
            'SIGN': sig(7, 1234567, 3561234)
        })
        xobj = xmltodict.parse(r.content)
        self.assertEqual(int(xobj['pay-response']['status_code']), 11)
        abon = Abon.objects.get(username='1234567')
        self.assertEqual(abon.ballance, 1)

    # пробуем добавить группу абонентов
    def test_add_abongroup(self):
        abon = Abon.objects.get(username='1234567')
        ag = AbonGroup.objects.create(title='%&34%$&*(')
        ag.profiles.add(abon)

    # пробуем добавить абонента
    def test_add_abon(self):
        c = Client()
        c.login(username='1234567', password='ps')
        r = c.get('/abons/1/addabon')
        # поглядим на страницу добавления абонента
        self.assertEqual(r.status_code, 200)
        r = c.post('/abons/1/addabon', {
            'username': '123',
            'password': 'ps',
            'fio': 'Abon Fio',
            'telephone': '+79783753914',
            'is_active': True
        })
        self.assertEqual(r.status_code, 302)
        r = c.get('/abons/324/addabon')
        self.assertEqual(r.status_code, 404)
        try:
            abn = Abon.objects.get(username='123')
            self.assertIsNotNone(abn)
            psw = AbonRawPassword.objects.get(account=abn, passw_text='ps')
            self.assertIsNotNone(psw)
        except Abon.DoesNotExist:
            # абонент должен был создаться
            self.assertTrue(False)
        except AbonRawPassword.DoesNotExist:
            # должен быть пароль абонента простым текстом
            self.assertTrue(False)


class AbonTariffTestCase(TestCase):
    def setUp(self):
        abon = Abon.objects.create(
            username='1234567',
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
