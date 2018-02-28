#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from json import dump
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
django.setup()
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
    res = [{
        'model': 'group_app.group',
        'pk': abon_group.pk,
        'fields': {
            'title': abon_group.title
        }
    } for abon_group in models.AbonGroup.objects.all()]

    #res += get_fixture_from_unchanget_model('abonapp.abonlog', models.AbonLog)

    res += get_fixture_from_unchanget_model('abonapp.abontariff', models.AbonTariff)

    res += get_fixture_from_unchanget_model('abonapp.abonstreet', models.AbonStreet)

    res += get_fixture_from_unchanget_model('abonapp.extrafieldsmodel', models.ExtraFieldsModel)

    res += get_fixture_from_unchanget_model('abonapp.abon', models.Abon)
    '''res += [{
        'model': 'abonapp.abon',
        'pk': ab.pk,
        'fields': {
            'current_tariff': ab.current_tariff.pk,
            'group': ab.group.pk,
            'ballance': ab.ballance,
            'ip_address': ab.ip_address,
            'description': ab.description,
            'street': ab.street,
            'house': ab.house,
            'extra_fields': [pid.pk for pid in ab.extra_fields.all()],
            'device': ab.device.pk,
            'dev_port': ab.dev_port.pk,
            'is_dynamic_ip': ab.is_dynamic_ip
        }
    } for ab in models.Abon.objects.all()]'''

    res += get_fixture_from_unchanget_model('abonapp.passportinfo', models.PassportInfo)

    res += get_fixture_from_unchanget_model('abonapp.invoiceforpayment', models.InvoiceForPayment)

    res += get_fixture_from_unchanget_model('abonapp.alltimepaylog', models.AllTimePayLog)

    res += get_fixture_from_unchanget_model('abonapp.abonrawpassword', models.AbonRawPassword)

    res += get_fixture_from_unchanget_model('abonapp.additionaltelephone', models.AdditionalTelephone)

    res += get_fixture_from_unchanget_model('abonapp.periodicpayforid', models.PeriodicPayForId)

    return res


def dump_tariffs():
    from tariff_app import models
    res = get_fixture_from_unchanget_model('tariff_app.Tariff', models.Tariff)

    res += get_fixture_from_unchanget_model('tariff_app.periodicpay', models.PeriodicPay)

    return res


def dump_devs():
    pass
    #from devapp import models



def make_migration():
    from datetime import datetime
    from datetime import date

    def my_date_converter(o):
        if isinstance(o, datetime) or isinstance(o, date):
            return "%s" % o

    def appdump(fname, func):
        with open(fname, 'w') as f:
            dump(func(), f, default=my_date_converter, ensure_ascii=False)

    appdump('abon_fixture.json', dump_abonapp)
    appdump('tariffs_fixture.json', dump_tariffs)



if __name__ == '__main__':
    make_migration()
