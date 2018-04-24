from hashlib import md5

from django.test import TestCase, RequestFactory
from django.conf import settings
from django.utils import timezone
from xmltodict import parse

from abonapp.models import Abon
from abonapp.pay_systems import allpay

rf = RequestFactory()
SERVICE_ID = getattr(settings, 'PAY_SERV_ID')
SECRET = getattr(settings, 'PAY_SECRET')


def _make_sign(act: int, pay_account: str, serv_id: str, pay_id):
    md = md5()
    s = "%d_%s_%s_%s_%s" % (act, pay_account, serv_id, pay_id, SECRET)
    md.update(bytes(s, 'utf-8'))
    return md.hexdigest()


class AllPayTestCase(TestCase):
    pay_url = '/'
    time_format = '%d.%m.%Y %H:%M'

    def setUp(self):
        a1 = Abon.objects.create_user(
            telephone='+79785276481',
            username='pay_account1',
            password='passw1'
        )
        a1.ballance = -13.12
        a1.fio = 'Test Name'
        a1.save(update_fields=['ballance', 'fio'])
        # Abon.objects.create_user(
        #    telephone='+79788163841',
        #    username='pay_account2',
        #    password='passw2'
        # )

    def user_pay_view(self):
        print('test_user_pay_view')
        current_date = timezone.now().strftime(self.time_format)
        r = allpay(rf.get(self.pay_url, {
                'ACT': 1,
                'PAY_ACCOUNT': 'pay_account1',
                'SERVICE_ID': SERVICE_ID,
                'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
                'TRADE_POINT': 'term1',
                'SIGN': _make_sign(1, 'pay_account1', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
            }
        ))
        r = r.content.decode('utf-8')
        self.assertXMLEqual(r, ''.join([
            "<pay-response>",
                "<balance>-13.12</balance>",
                "<name>Test Name</name>",
                "<account>pay_account1</account>",
                "<service_id>%s</service_id>" % SERVICE_ID,
                "<min_amount>10.0</min_amount>",
                "<max_amount>5000</max_amount>",
                "<status_code>21</status_code>",
                "<time_stamp>%s</time_stamp>" % current_date,
            "</pay-response>"
        ]))

    def user_pay_pay(self):
        print('test_user_pay_pay')
        current_date = timezone.now().strftime(self.time_format)
        r = allpay(rf.get(self.pay_url, {
            'ACT': 4,
            'PAY_ACCOUNT': 'pay_account1',
            'PAY_AMOUNT': 18.21,
            'RECEIPT_NUM': 2126235,
            'SERVICE_ID': SERVICE_ID,
            'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
            'TRADE_POINT': 'term1',
            'SIGN': _make_sign(4, 'pay_account1', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
        }))
        r = r.content.decode('utf-8')
        xml = ''.join([
            "<pay-response>",
                "<pay_id>840ab457-e7d1-4494-8197-9570da035170</pay_id>",
                "<service_id>%s</service_id>" % SERVICE_ID,
                "<amount>18.21</amount>",
                "<status_code>22</status_code>",
                "<time_stamp>%s</time_stamp>" % current_date,
            "</pay-response>"
        ])
        self.test_pay_time = current_date
        self.assertXMLEqual(r, xml)

    def user_pay_check(self):
        print('test_user_pay_check')
        current_date = timezone.now().strftime(self.time_format)
        r = allpay(rf.get(self.pay_url,
            {
                'ACT': 7,
                'SERVICE_ID': SERVICE_ID,
                'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
                'SIGN': _make_sign(7, '', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
            }
        ))
        r = r.content.decode('utf-8')
        xml = ''.join([
            "<pay-response>",
                "<status_code>11</status_code>",
                "<time_stamp>%s</time_stamp>" % current_date,
                "<transaction>",
                    "<pay_id>840ab457-e7d1-4494-8197-9570da035170</pay_id>",
                    "<service_id>%s</service_id>" % SERVICE_ID,
                    "<amount>18.21</amount>",
                    "<status>111</status>",
                    "<time_stamp>%s</time_stamp>" % self.test_pay_time,
                "</transaction>"
            "</pay-response>"
        ])
        self.assertXMLEqual(r, xml)

    def check_ballance(self):
        print('check_ballance')
        r = allpay(rf.get(self.pay_url,
            {
                'ACT': 1,
                'PAY_ACCOUNT': 'pay_account1',
                'SERVICE_ID': SERVICE_ID,
                'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
                'TRADE_POINT': 'term1',
                'SIGN': _make_sign(1, 'pay_account1', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
            }
        ))
        r = r.content.decode('utf-8')
        r = parse(r)
        bl = float(r['pay-response']['balance'])
        self.assertEqual(bl, 5.09)

    def test_client_does_not_exist(self):
        print('test_client_does_not_exist')
        current_date = timezone.now().strftime(self.time_format)
        r = allpay(rf.get(self.pay_url, {
            'ACT': 1,
            'PAY_ACCOUNT': 'not_existing_acc',
            'SERVICE_ID': SERVICE_ID,
            'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
            'TRADE_POINT': 'term1',
            'SIGN': _make_sign(1, 'not_existing_acc', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
        }
                          ))
        r = r.content.decode('utf-8')
        self.assertXMLEqual(r, ''.join([
            "<pay-response>",
                "<status_code>-40</status_code>",
                "<time_stamp>%s</time_stamp>" % current_date,
            "</pay-response>"
        ]))

    def try_pay_double(self):
        print('try_pay_double')
        r = allpay(rf.get(self.pay_url, {
            'ACT': 4,
            'PAY_ACCOUNT': 'pay_account1',
            'SERVICE_ID': SERVICE_ID,
            'PAY_ID': '840ab457-e7d1-4494-8197-9570da035170',
            'TRADE_POINT': 'term1',
            'SIGN': _make_sign(4, 'pay_account1', SERVICE_ID, '840ab457-e7d1-4494-8197-9570da035170')
        }))
        r = r.content.decode('utf-8')
        r = parse(r)
        status_code = int(r['pay-response']['status_code'])
        self.assertEqual(status_code, -100)

    def non_existing_pay(self):
        print('non_existing_pay')
        current_date = timezone.now().strftime(self.time_format)
        uuid = '9f154e93-d800-419a-92f7-da33529138be'
        r = allpay(rf.get(self.pay_url, {
            'ACT': 7,
            'SERVICE_ID': SERVICE_ID,
            'PAY_ID': uuid,
            'SIGN': _make_sign(7, '', SERVICE_ID, uuid)
        }))
        r = r.content.decode('utf-8')
        xml = ''.join([
            "<pay-response>",
                "<status_code>-10</status_code>",
                "<time_stamp>%s</time_stamp>" % current_date,
            "</pay-response>"
        ])
        self.assertXMLEqual(r, xml)

    def test_pays(self):
        self.user_pay_view()
        self.user_pay_pay()
        self.user_pay_check()
        self.check_ballance()
        self.try_pay_double()
        self.non_existing_pay()
