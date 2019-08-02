#!/usr/bin/env python
import os
from json import dump
from django import setup


class BatchSaveStreamList(list):
    def __init__(self, model_class, model_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_class = model_class
        self._model_name = model_name

    def __iter__(self):
        def fields(obj):
            return {ob.name: getattr(obj, ob.name) or None for ob in obj._meta.concrete_fields if ob.name != 'id'}

        for d in self._model_class.objects.all().iterator():
            yield {
                "model": self._model_name,
                "pk": d.pk,
                "fields": fields(d)
            }

    def __len__(self):
        return 1


def batch_save(fname, model_class, model_name):
    sa = BatchSaveStreamList(
        model_class=model_class,
        model_name=model_name
    )
    with open(fname, 'w') as f:
        dump(sa, f, ensure_ascii=False, indent=2)


# ---------------------


def dump_groups():
    from group_app.models import Group
    batch_save("groups.json", Group, 'groupapp.group')


def dump_accounts():
    from accounts_app.models import UserProfile, BaseAccount
    batch_save('accounts_baseaccount.json', BaseAccount, 'profiles.baseaccount')
    batch_save('accounts_userprofile.json', UserProfile, 'profiles.userprofile')


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djing.settings')
    setup()
    dump_groups()
