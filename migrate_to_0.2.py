#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import shutil
from json import dump
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
from django.db.models import fields as django_fields


def get_fixture_from_unchanget_model(model_name: str, model_class):
    """
    Создаёт фикстуру если модели между версиями не изменились
    :param model_name: str 'app_label.model_name'
    :param model_class: Model модель для которой надо сделать фикстуру
    :return: список словарей
    """
    print(model_name)

    def get_fields(obj):
        fields = dict()
        for field in obj._meta.get_fields():
            if isinstance(field, django_fields.reverse_related.ManyToOneRel) or \
                    isinstance(field, django_fields.reverse_related.ManyToManyRel):
                continue
            field_val = getattr(obj, field.name)
            if field_val is None:
                continue
            if isinstance(field, django_fields.related.ManyToManyField):
                fields[field.name] = [f.pk for f in field_val.all()]
            elif isinstance(field, django_fields.related.ForeignKey):
                fields[field.name] = field_val.pk
            elif isinstance(field, django_fields.FloatField):
                fields[field.name] = float(field_val)
            elif isinstance(field, django_fields.DateTimeField):
                fields[field.name] = str(field_val)
            elif isinstance(field, django_fields.AutoField):
                continue
            else:
                fields[field.name] = field_val
        return fields

    res = [{
        'model': model_name,
        'pk': obj.pk,
        'fields': get_fields(obj)
    } for obj in model_class.objects.all()]
    return res


def dump_abonapp():
    from abonapp import models
    print('group_app.group')
    res = [{
        'model': 'group_app.group',
        'pk': abon_group.pk,
        'fields': {
            'title': abon_group.title
        }
    } for abon_group in models.AbonGroup.objects.all()]

    # res += get_fixture_from_unchanget_model('abonapp.abonlog', models.AbonLog)

    res += get_fixture_from_unchanget_model('abonapp.abontariff', models.AbonTariff)

    res += get_fixture_from_unchanget_model('abonapp.abonstreet', models.AbonStreet)

    res += get_fixture_from_unchanget_model('abonapp.extrafieldsmodel', models.ExtraFieldsModel)

    res += get_fixture_from_unchanget_model('abonapp.abon', models.Abon)

    res += get_fixture_from_unchanget_model('abonapp.passportinfo', models.PassportInfo)

    res += get_fixture_from_unchanget_model('abonapp.invoiceforpayment', models.InvoiceForPayment)

    res += get_fixture_from_unchanget_model('abonapp.alltimepaylog', models.AllTimePayLog)

    res += get_fixture_from_unchanget_model('abonapp.abonrawpassword', models.AbonRawPassword)

    res += get_fixture_from_unchanget_model('abonapp.additionaltelephone', models.AdditionalTelephone)

    res += get_fixture_from_unchanget_model('abonapp.periodicpayforid', models.PeriodicPayForId)

    return res


def dump_tariffs():
    from tariff_app import models
    res = get_fixture_from_unchanget_model('tariff_app.tariff', models.Tariff)

    res += get_fixture_from_unchanget_model('tariff_app.periodicpay', models.PeriodicPay)

    return res


def dump_devs():
    from devapp import models
    print('devapp.device')
    res = [{
        'model': 'devapp.device',
        'pk': dv.pk,
        'fields': {
            'ip_address': dv.ip_address,
            'mac_addr': dv.mac_addr,
            'devtype': dv.devtype,
            'man_passw': dv.man_passw,
            'group': dv.user_group.pk if dv.user_group else 0,
            'parent_dev': dv.parent_dev.pk if dv.parent_dev else 0
        }
    } for dv in models.Device.objects.all()]

    res += get_fixture_from_unchanget_model('devapp.port', models.Port)
    return res


def dump_accounts():
    from accounts_app import models
    from abonapp.models import AbonGroup

    def get_responsibility_groups(account):
        responsibility_groups = AbonGroup.objects.filter(profiles__in=[account])
        ids = [ag.pk for ag in responsibility_groups]
        return ids

    print('accounts_app.userprofile')
    res = [{
        'model': 'accounts_app.userprofile',
        'pk': up.pk,
        'fields': {
            'username': up.username,
            'fio': up.fio,
            'birth_day': up.birth_day,
            'is_active': up.is_active,
            'is_admin': up.is_admin,
            'telephone': up.telephone,
            'avatar': up.avatar.pk if up.avatar else 0,
            'email': up.email,
            'responsibility_groups': get_responsibility_groups(up)
        }
    } for up in models.UserProfile.objects.filter(is_admin=True)]

    return res


def dump_photos():
    from photo_app.models import Photo
    res = get_fixture_from_unchanget_model('photo_app.photo', Photo)
    return res


def dump_chatbot():
    from chatbot import models
    res = get_fixture_from_unchanget_model('chatbot.telegrambot', models.TelegramBot)
    res += get_fixture_from_unchanget_model('chatbot.messagehistory', models.MessageHistory)
    res += get_fixture_from_unchanget_model('chatbot.messagequeue', models.MessageQueue)
    return res


def dump_map():
    from mapapp import models
    res = get_fixture_from_unchanget_model('mapapp.dot', models.Dot)
    return res


def dump_messages():
    from msg_app import models
    res = get_fixture_from_unchanget_model('msg_app.messagestatus', models.MessageStatus)
    res += get_fixture_from_unchanget_model('msg_app.message', models.Message)
    res += get_fixture_from_unchanget_model('msg_app.conversationmembership', models.ConversationMembership)
    res += get_fixture_from_unchanget_model('msg_app.conversation', models.Conversation)
    return res


def dump_task_app():
    from taskapp import models
    res = get_fixture_from_unchanget_model('taskapp.changelog', models.ChangeLog)
    res += get_fixture_from_unchanget_model('taskapp.task', models.Task)
    res += get_fixture_from_unchanget_model('taskapp.ExtraComment', models.ExtraComment)
    return res


def make_migration():
    from datetime import datetime
    from datetime import date

    def my_date_converter(o):
        if isinstance(o, datetime) or isinstance(o, date):
            return "%s" % o

    def appdump(path, func):
        fname = os.path.join(*path)
        path_dir = os.path.join(*path[:-1])
        if not os.path.isdir(path_dir):
            os.mkdir(path_dir)
        with open(fname, 'w') as f:
            dump(func(), f, default=my_date_converter, ensure_ascii=False)

    django.setup()
    appdump(['fixtures', 'tariff_app', 'tariffs_fixture.json'], dump_tariffs)
    appdump(['fixtures', 'photo_app', 'photos_fixture.json'], dump_photos)
    appdump(['fixtures', 'devapp', 'devs_fixture.json'], dump_devs)
    appdump(['fixtures', 'abonapp', 'abon_fixture.json'], dump_abonapp)
    appdump(['fixtures', 'accounts_app', 'accounts_fixture.json'], dump_accounts)

    appdump(['fixtures', 'chatbot', 'chatbot_fixture.json'], dump_chatbot)
    appdump(['fixtures', 'mapapp', 'map_fixture.json'], dump_map)
    appdump(['fixtures', 'msg_app', 'mesages_fixture.json'], dump_messages)
    appdump(['fixtures', 'taskapp', 'task_fixture.json'], dump_task_app)


def move_to_fixtures_dirs():
    fixdir = 'fixtures'
    for dr in os.listdir(fixdir):
        fixture_dir = os.path.join(fixdir, dr)
        fixture_file = os.listdir( fixture_dir )[0]
        from_file = os.path.join(fixture_dir, fixture_file)
        dst_dir = os.path.join(dr, fixdir)
        to_file = os.path.join(dst_dir, fixture_file)
        if not os.path.isdir( dst_dir ):
            os.mkdir(dst_dir)
        shutil.copyfile( from_file, to_file )
        print('cp %s -> %s' % (from_file, to_file))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: ./migrate_to_0.2.py [makedump OR applydump]')
        exit(1)
    choice = sys.argv[1]
    if choice == 'applydump':
        move_to_fixtures_dirs()
        print('And now apply created fixtures by ./manage.py loaddata')
    elif choice == 'makedump':
        make_migration()
    else:
        print('Unexpected choice')
