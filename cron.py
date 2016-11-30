#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from abonapp.models import Abon, AbonTariff

    users = Abon.objects.all()

    for usr in users:
        usr.activate_next_tariff()

        AbonTariff.objects.update_priorities(usr)
