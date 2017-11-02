# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from abonapp.models import Abon
from django.conf import settings


# От сюда можно получать на клиентской стороне профиль абонента
def context_processor_additional_profile(request):
    if request.user.is_staff or request.user.is_anonymous():
        return {'subscriber': request.user, 'FILE_UPLOAD_MAX_MEMORY_SIZE': settings.FILE_UPLOAD_MAX_MEMORY_SIZE}
    else:
        return {'subscriber': get_object_or_404(Abon, id=request.user.pk), 'FILE_UPLOAD_MAX_MEMORY_SIZE': settings.FILE_UPLOAD_MAX_MEMORY_SIZE}
