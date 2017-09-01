#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from abonapp.models import Abon
from agent import Transmitter, NasNetworkError, NasFailedResult
from mydefs import LogicError


def main():
    users = Abon.objects.all()
    for user in users:
        try:
            # бдим за услугами абонента
            user.bill_service(user)

            # если нет ip то и нет смысла лезть в NAS
            if user.ip_address is None:
                continue

            # а есть-ли у абонента доступ к услуге
            if not user.is_access():
                continue

            # строим структуру агента
            ab = user.build_agent_struct()
            if ab is None:
                # если не построилась структура агента, значит нет ip
                # а если нет ip то и синхронизировать абонента без ip нельзя
                continue

            # обновляем абонента если он статический. Иначе его обновит dhcp
            #if tm is None:
            #    tm = Transmitter()
            #tm.update_user(ab)

        except (NasNetworkError, NasFailedResult) as er:
            print("Error:", er)
        except LogicError as er:
            print("Notice:", er)
    tm = Transmitter()
    users = Abon.objects.filter(is_dynamic_ip=False)
    tm.sync_nas(users)


if __name__ == "__main__":
    try:
        main()
    except (NasNetworkError, NasFailedResult) as e:
        print('NAS:', e)
