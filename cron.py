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
    try:
        users = Abon.objects.filter(is_active=True, is_admin=False).exclude(ip_address=None)
        tm = Transmitter()
        tm.sync_nas(users)

    except (NasNetworkError, NasFailedResult) as er:
        print("Error:", er)
        exit(1)
    except LogicError as er:
        print("Notice:", er)
        exit(1)

if __name__ == "__main__":
    try:
        main()
    except (NasNetworkError, NasFailedResult) as e:
        print('NAS:', e)
