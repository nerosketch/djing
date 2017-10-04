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

        except (NasNetworkError, NasFailedResult) as er:
            print("Error:", er)
        except LogicError as er:
            print("Notice:", er)
    tm = Transmitter()
    users = Abon.objects.filter(is_dynamic_ip=False, is_active=True).exclude(current_tariff=None)
    tm.sync_nas(users)


if __name__ == "__main__":
    try:
        main()
    except (NasNetworkError, NasFailedResult) as e:
        print("Error while sync nas:", e)
    except LogicError as e:
        print("Notice while sync nas:", e)
