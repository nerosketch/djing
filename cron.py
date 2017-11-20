#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from django.utils import timezone
from django.db.models import signals
from abonapp.models import Abon, AbonTariff, abontariff_pre_delete
from agent import Transmitter, NasNetworkError, NasFailedResult
from mydefs import LogicError


def main():
    signals.pre_delete.disconnect(abontariff_pre_delete, sender=AbonTariff)
    AbonTariff.objects.filter(deadline__lt=timezone.now()).delete()
    tm = Transmitter()
    users = Abon.objects.filter(is_dynamic_ip=False, is_active=True).exclude(current_tariff=None)
    tm.sync_nas(users)
    signals.pre_delete.connect(abontariff_pre_delete, sender=AbonTariff)


if __name__ == "__main__":
    try:
        main()
    except (NasNetworkError, NasFailedResult) as e:
        print("Error while sync nas:", e)
    except LogicError as e:
        print("Notice while sync nas:", e)
