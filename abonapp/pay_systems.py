from hashlib import md5
from django.utils import timezone
from mydefs import safe_int, safe_float
from .models import Abon, AllTimePayLog
from django.db import DatabaseError
from django.conf import settings
from xmlview.decorators import xml_view

SECRET = getattr(settings, 'PAY_SECRET')
SERV_ID = getattr(settings, 'PAY_SERV_ID')


@xml_view(root_node='pay-response')
def allpay(request):
    def bad_ret(err_id, err_description=None):
        now = timezone.now()
        r = {
            'status_code': safe_int(err_id),
            'time_stamp': now.strftime("%d.%m.%Y %H:%M")
        }
        if err_description:
            r.update({'description': err_description})
        return r

    try:
        serv_id = request.GET.get('SERVICE_ID')
        act = safe_int(request.GET.get('ACT'))
        pay_account = request.GET.get('PAY_ACCOUNT')
        pay_id = request.GET.get('PAY_ID')
        pay_amount = safe_float(request.GET.get('PAY_AMOUNT'))
        sign = request.GET.get('SIGN').lower()
        current_date = timezone.now().strftime("%d.%m.%Y %H:%M")

        if act <= 0:
            return bad_ret(-101, 'ACT less than zero')

        # check sign
        md = md5()
        s = '_'.join((str(act), pay_account or '', serv_id or '', pay_id, SECRET))
        md.update(bytes(s, 'utf-8'))
        our_sign = md.hexdigest()
        if our_sign != sign:
            return bad_ret(-101)

        if act == 1:
            abon = Abon.objects.get(username=pay_account)
            fio = abon.fio
            ballance = float(abon.ballance)
            return {
                'balance': ballance,
                'name': fio,
                'account': pay_account,
                'service_id': SERV_ID,
                'min_amount': 10.0,
                'max_amount': 5000,
                'status_code': 21,
                'time_stamp': current_date
            }
        elif act == 4:
            trade_point = safe_int(request.GET.get('TRADE_POINT'))
            receipt_num = safe_int(request.GET.get('RECEIPT_NUM'))
            abon = Abon.objects.get(username=pay_account)
            pays = AllTimePayLog.objects.filter(pay_id=pay_id)
            if pays.count() > 0:
                return bad_ret(-100)

            abon.add_ballance(None, pay_amount, comment='AllPay %.2f' % pay_amount)
            abon.save(update_fields=('ballance',))

            AllTimePayLog.objects.create(
                pay_id=pay_id,
                summ=pay_amount,
                abon=abon,
                trade_point=trade_point,
                receipt_num=receipt_num
            )
            return {
                'pay_id': pay_id,
                'service_id': serv_id,
                'amount': pay_amount,
                'status_code': 22,
                'time_stamp': current_date
            }
        elif act == 7:
            pay = AllTimePayLog.objects.get(pay_id=pay_id)
            return {
                'status_code': 11,
                'time_stamp': current_date,
                'transaction': {
                    'pay_id': pay_id,
                    'service_id': serv_id,
                    'amount': pay.summ,
                    'status': 111,
                    'time_stamp': pay.date_add.strftime("%d.%m.%Y %H:%M")
                }
            }
        else:
            return bad_ret(-101, 'ACT is not passed')

    except Abon.DoesNotExist:
        return bad_ret(-40)
    except DatabaseError:
        return bad_ret(-90)
    except AllTimePayLog.DoesNotExist:
        return bad_ret(-10)
    except AttributeError:
        return bad_ret(-101)
