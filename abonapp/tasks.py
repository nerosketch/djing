from celery import shared_task

from abonapp.models import Abon
from djing.lib import LogicError
from gw_app.models import NASModel
from gw_app.nas_managers import NasFailedResult, NasNetworkError, SubnetQueue


@shared_task
def customer_nas_command(customer_uid: int, command: str):
    if command not in ('add', 'sync'):
        return 'Command required'
    try:
        cust = Abon.objects.get(pk=customer_uid)
        print(cust, command)
        if command == 'sync':
            r = cust.nas_sync_self()
            if isinstance(r, Exception):
                return 'ABONAPP SYNC ERROR: %s' % r
        elif command == 'add':
            cust.nas_add_self()
        else:
            return 'ABONAPP SYNC ERROR: Unknown command "%s"' % command
    except Abon.DoesNotExist:
        pass
    except (LogicError, NasFailedResult, NasNetworkError, ConnectionResetError) as e:
        return 'ABONAPP ERROR: %s' % e


@shared_task
def customer_nas_remove(customer_uid: int, ip_addr: str, speed: tuple, is_access: bool, nas_pk: int):
    try:
        if not isinstance(ip_addr, (str, int)):
            ip_addr = str(ip_addr)
        sq = SubnetQueue(
            name="uid%d" % customer_uid,
            network=ip_addr,
            max_limit=speed,
            is_access=is_access
        )
        nas = NASModel.objects.get(pk=nas_pk)
        mngr = nas.get_nas_manager()
        mngr.remove_user(sq)
    except (ValueError, NasFailedResult, NasNetworkError, LogicError) as e:
        return 'ABONAPP ERROR: %s' % e
    except NASModel.DoesNotExist:
        return 'NASModel.DoesNotExist id=%d' % nas_pk
