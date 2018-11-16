from celery import shared_task
from abonapp.models import Abon
from djing.lib import LogicError
from gw_app.nas_managers import NasFailedResult, NasNetworkError


@shared_task
def user_remove_from_gw(user_id: int):
    try:
        user = Abon.objects.get(pk=user_id)
        agent_abon = user.build_agent_struct()
        if agent_abon is not None:
            mngr = user.nas.get_nas_manager()
            mngr.remove_user(agent_abon)
    except (
            Abon.DoesNotExist, NasFailedResult,
            NasNetworkError, ConnectionResetError, LogicError
    ):
        pass


@shared_task
def user_add_to_gw(user_id: int):
    try:
        user = Abon.objects.get(pk=user_id)
        agent_abon = user.build_agent_struct()
        if agent_abon is not None:
            mngr = user.nas.get_nas_manager()
            mngr.add_user(agent_abon)
    except (
            Abon.DoesNotExist, NasFailedResult,
            NasNetworkError, ConnectionResetError, LogicError
    ):
        pass


@shared_task
def user_nas_sync(user_id: int):
    try:
        user = Abon.objects.get(pk=user_id)
        agent_abon = user.build_agent_struct()
        if agent_abon is not None:
            mngr = user.nas.get_nas_manager()
            mngr.update_user(agent_abon)
    except (NasFailedResult, NasNetworkError, ConnectionResetError, LogicError) as e:
        return 'ERROR:%s' % e
