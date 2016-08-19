# -*- coding:utf-8 -*-
import requests
from json import loads
from models import deserialize_tariffs, deserialize_abonents
import settings


def load_from_db():
    r = requests.get('%s://%s:%d/abons/api/abons' % (
        'https' if settings.IS_USE_SSL else 'http',
        settings.SERVER_IP,
        settings.SERVER_PORT
    ), verify=False)
    try:
        user_data = loads(r.text)
        del r
        # Получаем тарифы
        tariffs = deserialize_tariffs(user_data)

        # Получаем пользователей
        abons = deserialize_abonents(user_data, tariffs)

        return abons, tariffs

    except ValueError as e:
        print 'Error:', e, r.text
        return
