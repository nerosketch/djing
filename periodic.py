#!/usr/bin/env python3
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
from django.utils import timezone
from django.db import transaction
from django.db.models import signals, Count
from abonapp.models import Abon, AbonTariff, abontariff_pre_delete, PeriodicPayForId, AbonLog
from ip_pool.models import IpLeaseModel
from agent import Transmitter, NasNetworkError, NasFailedResult
from djing.lib import LogicError


def main():
    signals.pre_delete.disconnect(abontariff_pre_delete, sender=AbonTariff)
    AbonTariff.objects.filter(abon=None).delete()
    now = timezone.now()
    fields = ('id', 'tariff__title', 'abon__id')
    expired_services = AbonTariff.objects.filter(deadline__lt=now).exclude(abon=None)

    # finishing expires services
    with transaction.atomic():
        for ex_srv in expired_services.only(*fields).values(*fields):
            log = AbonLog.objects.create(
                abon_id=ex_srv['abon__id'],
                amount=0,
                author=None,
                date=now,
                comment="Срок действия услуги '%(service_name)s' истёк" % {
                    'service_name': ex_srv['tariff__title']
                }
            )
            print(log)
        expired_services.delete()
    signals.pre_delete.connect(abontariff_pre_delete, sender=AbonTariff)

    # sync subscribers on NAS
    try:
        tm = Transmitter()
        users = Abon.objects\
            .filter(is_active=True, ips_count__gt=0)\
            .exclude(current_tariff=None)\
            .annotate(ips_count=Count('ip_addresses'))\
            .prefetch_related('ip_addresses')\
            .iterator()
        tm.sync_nas(users)
    except NasNetworkError as er:
        print('NetworkTrouble:', er)

    # manage periodic pays
    ppays = PeriodicPayForId.objects.filter(next_pay__lt=now) \
        .prefetch_related('account', 'periodic_pay')
    for pay in ppays:
        pay.payment_for_service(now=now)

    # Remove old inactive ip leases
    old_leases = IpLeaseModel.objects.expired()
    old_leases.delete()


if __name__ == "__main__":
    try:
        main()
    except (NasNetworkError, NasFailedResult) as e:
        print("Error while sync nas:", e)
    except LogicError as e:
        print("Notice while sync nas:", e)
