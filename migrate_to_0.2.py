#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import shutil
from json import dump
import django

'''
Some permissions is not migrates, all admins is superuser
after migrate.
'''

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
            if isinstance(field,
                          (django_fields.reverse_related.ManyToOneRel, django_fields.reverse_related.ManyToManyRel)):
                continue
            field_val = getattr(obj, field.name)
            if field_val is None:
                continue
            if isinstance(field, django_fields.related.ManyToManyField):
                fields[field.name] = [f.pk for f in field_val.all()]
            elif isinstance(field,
                            (django_fields.related.ForeignKey, django.contrib.contenttypes.fields.GenericForeignKey)):
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


def dump_groups():
    from abonapp import models
    print('group_app.group')
    res = [{
        'model': 'group_app.group',
        'pk': abon_group.pk,
        'fields': {
            'title': abon_group.title
        }
    } for abon_group in models.AbonGroup.objects.all()]
    return res


def dump_abonapp():
    from abonapp import models

    res = get_fixture_from_unchanget_model('abonapp.abontariff', models.AbonTariff)

    res += get_fixture_from_unchanget_model('abonapp.abonstreet', models.AbonStreet)

    res += get_fixture_from_unchanget_model('abonapp.extrafieldsmodel', models.ExtraFieldsModel)

    # res += get_fixture_from_unchanget_model('abonapp.abonlog', models.AbonLog)

    print('abonapp.abon')
    res += [{
        'model': 'abonapp.abon',
        'pk': abon.pk,
        'fields': {
            'current_tariff': abon.current_tariff.pk if abon.current_tariff else None,
            'group': abon.group.pk if abon.group else None,
            'ballance': abon.ballance,
            'ip_address': abon.ip_address,
            'description': abon.description,
            'street': abon.street.pk if abon.street else None,
            'house': abon.house,
            'extra_fields': [a.pk for a in abon.extra_fields.all()],
            'device': abon.device.pk if abon.device else None,
            'dev_port': abon.dev_port if abon.dev_port else None,
            'is_dynamic_ip': abon.is_dynamic_ip,
            'markers': abon.markers
        }
    } for abon in models.Abon.objects.filter(is_admin=False)]

    res += get_fixture_from_unchanget_model('abonapp.passportinfo', models.PassportInfo)

    res += get_fixture_from_unchanget_model('abonapp.invoiceforpayment', models.InvoiceForPayment)

    res += get_fixture_from_unchanget_model('abonapp.alltimepaylog', models.AllTimePayLog)

    res += get_fixture_from_unchanget_model('abonapp.abonrawpassword', models.AbonRawPassword)

    res += get_fixture_from_unchanget_model('abonapp.additionaltelephone', models.AdditionalTelephone)

    res += get_fixture_from_unchanget_model('abonapp.periodicpayforid', models.PeriodicPayForId)

    return res


def dump_tariffs():
    from tariff_app import models
    from abonapp.models import AbonGroup
    print('tariff_app.tariff')
    res = [{
        'model': 'tariff_app.tariff',
        'pk': trf.pk,
        'fields': {
            'title': trf.title,
            'descr': trf.descr,
            'speedIn': trf.speedIn,
            'speedOut': trf.speedOut,
            'amount': trf.amount,
            'calc_type': trf.calc_type,
            'is_admin': trf.is_admin,
            'groups': [ag.pk for ag in AbonGroup.objects.filter(tariffs__in=[trf])]
        }
    } for trf in models.Tariff.objects.all()]

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
            'mac_addr': str(dv.mac_addr) if dv.mac_addr else None,
            'comment': dv.comment,
            'devtype': dv.devtype,
            'man_passw': dv.man_passw,
            'group': dv.user_group.pk if dv.user_group else None,
            'parent_dev': dv.parent_dev.pk if dv.parent_dev else None,
            'snmp_item_num': dv.snmp_item_num,
            'status': dv.status,
            'is_noticeable': dv.is_noticeable
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

    print('accounts_app.baseaccount')
    res = [{
        'model': 'accounts_app.baseaccount',
        'pk': up.pk,
        'fields': {
            'username': up.username,
            'fio': up.fio,
            'birth_day': up.birth_day,
            'is_active': up.is_active,
            'is_admin': up.is_admin,
            'telephone': up.telephone,
            'password': up.password,
            'last_login': up.last_login,
            'is_superuser': up.is_admin
        }
    } for up in models.UserProfile.objects.all()]

    print('accounts_app.userprofile')
    res += [{
        'model': 'accounts_app.userprofile',
        'pk': up.pk,
        'fields': {
            'avatar': up.avatar.pk if up.avatar else None,
            'email': up.email,
            'responsibility_groups': get_responsibility_groups(up)
        }
    } for up in models.UserProfile.objects.filter(is_admin=True)]

    return res


def dump_photos():
    from photo_app.models import Photo
    print('photo_app.photo')
    res = [{
        'model': 'photo_app.photo',
        'pk': p.pk,
        'fields': {
            'image': "%s" % p.image,
            'wdth': p.wdth,
            'heigt': p.heigt
        }
    } for p in Photo.objects.all()]
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


def dump_task_app():
    from taskapp import models
    res = get_fixture_from_unchanget_model('taskapp.changelog', models.ChangeLog)
    res += get_fixture_from_unchanget_model('taskapp.task', models.Task)
    res += get_fixture_from_unchanget_model('taskapp.ExtraComment', models.ExtraComment)
    return res


def dump_auth():
    from django.contrib.auth import models
    from django.contrib.contenttypes.models import ContentType
    res = get_fixture_from_unchanget_model('contenttypes.contenttype', ContentType)
    res += get_fixture_from_unchanget_model('auth.group', models.Group)
    res += get_fixture_from_unchanget_model('auth.permission', models.Permission)
    return res


def dump_guardian():
    from guardian import models
    print('guardian.groupobjectpermission')
    res = [{
        'model': 'guardian.groupobjectpermission',
        'pk': gp.pk,
        'fields': {
            'group': gp.group.pk,
            'permission': gp.permission.pk,
            'content_type': gp.content_type.pk,
            'object_pk': str(gp.object_pk),
            'content_object': gp.content_object.pk
        }
    } for gp in models.GroupObjectPermission.objects.all()]
    print('guardian.userobjectpermission')
    res += [{
        'model': 'guardian.userobjectpermission',
        'pk': up.pk,
        'fields': {
            'permission': up.permission.pk,
            'content_type': up.content_type.pk,
            'object_pk': str(up.object_pk),
            'user': up.user.pk
        }
    } for up in models.UserObjectPermission.objects.all()]
    return res


def make_migration():
    from datetime import datetime, date

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

    if not os.path.isdir('fixtures'):
        os.mkdir('fixtures')
    appdump(['fixtures', 'group_app', 'groups_fixture.json'], dump_groups)
    appdump(['fixtures', 'tariff_app', 'tariffs_fixture.json'], dump_tariffs)
    appdump(['fixtures', 'photo_app', 'photos_fixture.json'], dump_photos)
    appdump(['fixtures', 'devapp', 'devs_fixture.json'], dump_devs)
    appdump(['fixtures', 'accounts_app', 'accounts_fixture.json'], dump_accounts)
    appdump(['fixtures', 'abonapp', 'abon_fixture.json'], dump_abonapp)
    appdump(['fixtures', 'chatbot', 'chatbot_fixture.json'], dump_chatbot)
    appdump(['fixtures', 'mapapp', 'map_fixture.json'], dump_map)
    appdump(['fixtures', 'taskapp', 'task_fixture.json'], dump_task_app)
    # appdump(['fixtures', 'accounts_app', 'auth_fixture.json'], dump_auth)
    # appdump(['fixtures', 'accounts_app', 'guardian_fixture.json'], dump_guardian)


def move_to_fixtures_dirs():
    fixdir = 'fixtures'
    for dr in os.listdir(fixdir):
        fixture_dir = os.path.join(fixdir, dr)
        for fixture_file in os.listdir(fixture_dir):
            from_file = os.path.join(fixture_dir, fixture_file)
            dst_dir = os.path.join(dr, fixdir)
            to_file = os.path.join(dst_dir, fixture_file)
            if not os.path.isdir(dst_dir):
                os.mkdir(dst_dir)
            shutil.copyfile(from_file, to_file)
            print('cp %s -> %s' % (from_file, to_file))


def apply_fixtures():
    from django.core.management import execute_from_command_line
    from accounts_app.models import UserProfile
    # from django.contrib.auth import models

    UserProfile.objects.filter(username='AnonymousUser').delete()
    # print('clearing auth.group')
    # models.Group.objects.all().delete()
    # print('clearing auth.permission')
    # models.Permission.objects.all().delete()

    fixtures_names = [
        'groups_fixture.json', 'tariffs_fixture.json', 'photos_fixture.json',
        'devs_fixture.json', 'accounts_fixture.json', 'abon_fixture.json',
        'chatbot_fixture.json', 'map_fixture.json', 'task_fixture.json'
    ]
    # 'auth_fixture.json', 'guardian_fixture.json'
    print('./manage.py loaddata ' + ', '.join(fixtures_names))
    execute_from_command_line([sys.argv[0], 'loaddata'] + fixtures_names)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: ./migrate_to_0.2.py [makedump OR applydump]')
        exit(1)
    choice = sys.argv[1]
    if choice == 'applydump':
        django.setup()
        move_to_fixtures_dirs()
        apply_fixtures()
        shutil.rmtree('fixtures')
    elif choice == 'makedump':
        django.setup()
        make_migration()
    else:
        print('Unexpected choice')
