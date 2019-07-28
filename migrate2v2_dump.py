#!/usr/bin/env python
import os
from json import dump

from bitfield import BitField
from django import setup
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ImageField, ManyToManyField

from djing.fields import MACAddressField


class BatchSaveStreamList(list):
    def __init__(self, model_class, model_name, except_fields=None, choice_list_map=None, field_name_map=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_class = model_class
        self._model_name = model_name
        self._except_fields = (except_fields or []) + ['id']
        self._choice_list_map = choice_list_map or {}
        self._field_name_map = field_name_map or {}
        print(model_name, end='\t'*3)

    def _map_field_name(self, name):
        if name in self._field_name_map:
            return self._field_name_map.get(name)
        return name

    def _fields(self, obj):
        fls = obj._meta.get_fields()
        return {self._map_field_name(ob.name): self._field_val(obj, ob) for ob in fls if
                ob.name not in self._except_fields}

    def __iter__(self):
        for d in self._model_class.objects.all().iterator():
            yield {
                "model": self._model_name,
                "pk": d.pk,
                "fields": self._fields(d)
            }

    def _field_val(self, obj, field):
        # choice fields
        if field.name in self._choice_list_map.keys():
            val = getattr(obj, field.name)
            return self._choice_list_map[field.name].get(val)

        # bit fields
        elif isinstance(field, BitField):
            val = getattr(obj, field.name)
            # val is instance of BitHandler
            return int(val)

        # image fields
        elif isinstance(field, ImageField):
            val = getattr(obj, field.name)
            if val._file:
                return val.url

        # mac address validated by netaddr.EUI
        elif isinstance(field, MACAddressField):
            val = getattr(obj, field.name)
            return str(val)

        # related fields
        if field.is_relation:
            val = getattr(obj, field.attname)
            if isinstance(field, ManyToManyField):
                s = val.only('pk').values_list('pk', flat=True)
                return tuple(s)
            return val

        # all other simple fields
        else:
            v = getattr(obj, field.name)
            if isinstance(v, bool):
                return v
            return v or None

    def __len__(self):
        return 1


def batch_save(fname, *args, **kwargs):
    sa = BatchSaveStreamList(*args, **kwargs)
    print(fname)
    with open(fname, 'w') as f:
        dump(sa, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)


# ---------------------


def dump_groups():
    from group_app.models import Group
    batch_save("groups.json", Group, 'groupapp.group')


def dump_accounts():
    from accounts_app.models import UserProfile, BaseAccount, UserProfileLog
    batch_save('accounts_baseaccount.json', BaseAccount, 'profiles.baseaccount')
    batch_save('accounts_userprofile.json', UserProfile, 'profiles.userprofile')
    do_type_map = {
        'cusr': 1,
        'dusr': 2,
        'cdev': 3,
        'ddev': 4,
        'cnas': 5,
        'dnas': 6,
        'csrv': 7,
        'dsrv': 8
    }
    batch_save('accounts_userprofilelog.json', UserProfileLog, 'profiles.userprofilelog',
               except_fields=['meta_info'],
               choice_list_map={
                   'do_type': do_type_map
               })


def dump_messenger():
    from messenger.models import Messenger, ViberMessenger, ViberMessage, ViberSubscriber
    batch_save("messenger.json", Messenger, 'messenger.messenger')
    batch_save("ViberMessenger.json", ViberMessenger, 'messenger.vibermessenger')
    batch_save("ViberMessage.json", ViberMessage, 'messenger.vibermessage')
    batch_save("ViberSubscriber.json", ViberSubscriber, 'messenger.vibersubscriber')


def dump_services():
    from tariff_app.models import Tariff, PeriodicPay
    batch_save("services.json", Tariff, 'services.service', field_name_map={
        'speedIn': 'speed_in',
        'speedOut': 'speed_out',
        'amount': 'cost'
    }, choice_list_map={
        'calc_type': {
            'Df': 0,
            'Dp': 1,
            'Cp': 2,
            'Dl': 3
        }
    })
    batch_save("services_periodicpay.json", PeriodicPay, 'services.periodicpay', choice_list_map={
        'calc_type': {
            'df': 0,
            'cs': 1
        }
    })


def dump_gateways():
    from gw_app.models import NASModel
    batch_save("gateways.json", NASModel, 'gateways.gateway', field_name_map={
        'nas_type': 'gw_type',
        'default': 'is_default'
    }, choice_list_map={
        'nas_type': {
            'mktk': 0
        }
    })


def dump_devices():
    from devapp.models import Device, Port
    batch_save("devices.json", Device, 'devices.device', field_name_map={
        'devtype': 'dev_type'
    }, choice_list_map={
        'devtype': {
            'Dl': 1, 'Pn': 2,
            'On': 3, 'Ex': 4,
            'Zt': 5, 'Zo': 6,
            'Z6': 7, 'Hw': 8
        },
        'status': {
            'und': 0,
            'up': 1,
            'unr': 2,
            'dwn': 3
        }
    })
    batch_save('devices_port.json', Port, 'devices.port')


def dump_customers():
    from abonapp.models import (
        Abon, AbonLog, AbonTariff, AbonStreet,
        PassportInfo, InvoiceForPayment, AbonRawPassword,
        AdditionalTelephone, PeriodicPayForId
    )
    batch_save('customers.json', Abon, 'customers.customer', field_name_map={
        'current_tariff': 'current_service',
        'ballance': 'balance',
        'nas': 'gateway',
        'autoconnect_service': 'auto_renewal_service',
        'last_connected_tariff': 'last_connected_service'
    })
    batch_save('customers_log.json', AbonLog, 'customers.customerlog', field_name_map={
        'abon': 'customer',
        'amount': 'cost'
    })
    batch_save('customers_service.json', AbonTariff, 'customers.customerservice', field_name_map={
        'tariff': 'service',
        'time_start': 'start_time'
    })
    batch_save('customers_street.json', AbonStreet, 'customers.customerstreet')
    batch_save('customers_passport.json', PassportInfo, 'customers.passportinfo', field_name_map={
        'abon': 'customer'
    })
    batch_save('customers_inv.json', InvoiceForPayment, 'customers.invoiceforpayment', field_name_map={
        'abon': 'customer',
        'amount': 'cost'
    })
    batch_save('customers_passw.json', AbonRawPassword, 'customers.customerrawpassword', field_name_map={
        'account': 'customer'
    })
    batch_save('customers_tels.json', AdditionalTelephone, 'customers.additionaltelephone', field_name_map={
        'abon': 'customer'
    })
    batch_save('customers_tels.json', PeriodicPayForId, 'customers.periodicpayforid')


def dump_networks():
    from ip_pool.models import NetworkModel
    batch_save('nets.json', NetworkModel, 'networks.networkmodel', choice_list_map={
        'kind': {
            'inet': 1,
            'guest': 2,
            'trust': 3,
            'device': 4,
            'admin': 5
        }
    })


def dump_tasks():
    from taskapp.models import Task, ExtraComment, ChangeLog
    batch_save('task.json', Task, 'tasks.task', field_name_map={
        'abon': 'customer'
    }, except_fields=['attachment'], choice_list_map={
        'priority': {
            'E': 0,
            'C': 1,
            'A': 2
        },
        'state': {
            'S': 0,
            'C': 1,
            'F': 2
        },
        'mode': {
            'na', 0, 'ic', 1,
            'yt', 2, 'rc', 3,
            'ls', 4, 'cf', 5,
            'cn', 6, 'pf', 7,
            'cr', 8, 'co', 9,
            'fc', 10, 'ni', 11,
            'ot', 12
        }
    })
    batch_save('task_comments.json', ExtraComment, 'tasks.extracomment')
    batch_save('task_log.json', ChangeLog, 'tasks.changelog', choice_list_map={
        'act_type': {
            'e': 1, 'c': 2,
            'd': 3, 'f': 4, 'b': 5
        }
    })


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djing.settings')
    setup()
    dump_tasks()
