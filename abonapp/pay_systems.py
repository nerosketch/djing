from hashlib import md5
from django.utils import timezone
from mydefs import safe_int, safe_float
from .models import Abon, AllTimePayLog
from django.db import DatabaseError


from djing.settings import pay_SECRET as SECRET, pay_SERV_ID as SERV_ID


#?ACT=1&PAY_ACCOUNT=960849&SERVICE_ID=y832r92y8f9e&PAY_ID=3561234&TRADE_POINT=377&SIGN=32e533a72389fe4e93746509f9d672f8
#?ACT=4&PAY_ACCOUNT=960849&PAY_AMOUNT=1.00&RECEIPT_NUM=29096&SERVICE_ID=y832r92y8f9e&PAY_ID=3561234&TRADE_POINT=496&SIGN=c42161214099dba01e6ab008552bbd3d


def allpay(request):

    def bad_ret(err_id):
        current_date = timezone.now()
        return "<?xml version='1.0' encoding='UTF-8'?>\n" \
               "<pay-response>\n" \
               "  <status_code>%d</status_code>\n" % safe_int(err_id) +\
               "  <time_stamp>%s</time_stamp>\n" % current_date.strftime("%d.%m.%Y %H:%M:%S") +\
               "</pay-response>"

    try:
        serv_id = request.GET.get('SERVICE_ID')
        act = safe_int(request.GET.get('ACT'))
        pay_account = safe_int(request.GET.get('PAY_ACCOUNT'))
        pay_id = request.GET.get('PAY_ID')
        pay_amount = safe_float(request.GET.get('PAY_AMOUNT'))
        sign = request.GET.get('SIGN').lower()

        # check sign
        md = md5()
        s = '_'.join((str(act), str(pay_account), serv_id or '', pay_id, SECRET))
        md.update(bytes(s, 'utf-8'))
        our_sign = md.hexdigest()
        if our_sign != sign:
            return bad_ret(-101)

        if act <= 0: return bad_ret(-101)
        if pay_account == 0: return bad_ret(-40)

        if act == 1:
            abon = Abon.objects.get(username=pay_account)
            fio = abon.fio
            ballance = float(abon.ballance)
            current_date = timezone.now().strftime("%d.%m.%Y %H:%M:%S")
            return "<?xml version='1.0' encoding='UTF-8'?>\n" \
                    "<pay-response>\n" \
                    "  <balance>%.2f</balance>\n" % ballance +\
                    "  <name>%s</name>\n" % fio +\
                    "  <account>%d</account>\n" % pay_account +\
                    "  <service_id>%s</service_id>\n" % SERV_ID +\
                    "  <min_amount>10.0</min_amount>\n" \
                    "  <max_amount>50000</max_amount>\n" \
                    "  <status_code>21</status_code>\n" \
                    "  <time_stamp>%s</time_stamp>\n" % current_date +\
                    "</pay-response>"
        elif act == 4:
            abon = Abon.objects.get(username=pay_account)
            pays = AllTimePayLog.objects.filter(pay_id=pay_id)
            if pays.count() > 0:
                return bad_ret(-100)

            # тут в author передаём учётку абонента, т.к. это он сам через терминал пополняет
            abon.add_ballance(abon, pay_amount, comment='AllPay %.2f' % pay_amount)
            abon.save(update_fields=['ballance'])

            AllTimePayLog.objects.create(
                pay_id=pay_id,
                summ=pay_amount
            )
            current_date = timezone.now().strftime("%d.%m.%Y %H:%M:%S")
            return "<?xml version='1.0' encoding='UTF-8'?>" \
                   "<pay-response>\n" +\
                   "  <pay_id>%s</pay_id>\n" % pay_id +\
                   "  <service_id>%s</service_id>\n" % serv_id +\
                   "  <amount>%.2f</amount>\n" % pay_amount +\
                   "  <status_code>22</status_code>\n" +\
                   "  <time_stamp>%s</time_stamp>\n" % current_date +\
                   "</pay-response>"
        elif act == 7:
            pay = AllTimePayLog.objects.get(pay_id=pay_id)
            current_date = timezone.now().strftime("%d.%m.%Y %H:%M:%S")
            return "<?xml version='1.0' encoding='UTF-8'?>\n" \
                   "<pay-response>\n" \
                   "  <status_code>11</status_code>\n" \
                   "  <time_stamp>%s</time_stamp>\n" % current_date +\
                   "  <transaction>\n" \
                   "    <pay_id>%s</pay_id>\n" % pay_id +\
                   "    <service_id>%s</service_id>\n" % serv_id +\
                   "    <amount>%.2f</amount>\n" % float(pay.summ) +\
                   "    <status>111</status>\n" +\
                   "    <time_stamp>%s</time_stamp>\n" % current_date +\
                   "  </transaction>\n" \
                   "</pay-response>"
        else:
            return bad_ret(-101)

    except Abon.DoesNotExist:
        return bad_ret(-40)
    except DatabaseError:
        return bad_ret(-90)
    except AllTimePayLog.DoesNotExist:
        return bad_ret(-10)
    except AttributeError:
        return bad_ret(-101)
