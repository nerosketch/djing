# -*- coding:utf-8 -*-
import requests
from json import loads
from requests.exceptions import ConnectionError
from models import deserialize_tariffs, deserialize_abonents
import settings


def load_from_db():
    try:
        r = requests.get('%s://%s:%d/abons/api/abons' % (
            'https' if settings.IS_USE_SSL else 'http',
            settings.SERVER_IP,
            settings.SERVER_PORT
        ), verify=False)
        user_data = loads(r.text)

        # Получаем тарифы
        tariffs = deserialize_tariffs(user_data)

        # Получаем пользователей
        abons = deserialize_abonents(user_data, tariffs)

        return abons, tariffs

    except ValueError as e:
        print('Error:', e, r.text)

    except ConnectionError:
        print("Can not connect to server %s:%d..." % (settings.SERVER_IP, settings.SERVER_PORT))
        exit(0)
