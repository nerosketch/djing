#!/usr/bin/env python
import os
from json import dump

from bitfield import BitField
from django import setup
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ImageField


class BatchSaveStreamList(list):
    def __init__(self, model_class, model_name, except_fields=None, list_map=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_class = model_class
        self._model_name = model_name
        self._except_fields = (except_fields or []) + ['id']
        self._list_map = list_map or {}

    def _fields(self, obj):
        return {ob.name: self._list_map_fn(obj, ob) for ob in obj._meta.concrete_fields if
                ob.name not in self._except_fields}

    def __iter__(self):
        for d in self._model_class.objects.all().iterator():
            yield {
                "model": self._model_name,
                "pk": d.pk,
                "fields": self._fields(d)
            }

    def _list_map_fn(self, obj, field):
        if field.is_relation:
            # fl = getattr(obj, field.name)
            val = getattr(obj, field.attname)
            return val
        elif field.name in self._list_map.keys():
            val = getattr(obj, field.name)
            return self._list_map.get(val)
        elif isinstance(field, BitField):
            val = getattr(obj, field.name)
            # val is instance of BitHandler
            return int(val)
        elif isinstance(field, ImageField):
            val = getattr(obj, field.name)
            if val._file:
                return val.url
        else:
            return getattr(obj, field.name) or None

    def __len__(self):
        return 1


def batch_save(fname, *args, **kwargs):
    sa = BatchSaveStreamList(*args, **kwargs)
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
               list_map={
                   'do_type': do_type_map
               })


def dump_messenger():
    from messenger.models import Messenger, ViberMessenger, ViberMessage, ViberSubscriber
    batch_save("messenger.json", Messenger, 'messenger.messenger')
    batch_save("ViberMessenger.json", ViberMessenger, 'messenger.vibermessenger')
    batch_save("ViberMessage.json", ViberMessage, 'messenger.vibermessage')
    batch_save("ViberSubscriber.json", ViberSubscriber, 'messenger.vibersubscriber')


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djing.settings')
    setup()
    dump_messenger()
