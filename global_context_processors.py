# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from abonapp.models import Abon


def context_processor_client_ipaddress(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    return {
        'client_ipaddress': ip
    }


# От сюда можно получать на клиентской стороне профиль абонента
def context_processor_additional_profile(request):
    if request.user.is_staff or request.user.is_anonymous():
        return {'subscriber': request.user}
    else:
        return {'subscriber': get_object_or_404(Abon, id=request.user.id)}
