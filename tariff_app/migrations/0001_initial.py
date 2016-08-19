# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-28 23:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tariff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=32)),
                ('speedIn', models.FloatField(default=0.0)),
                ('speedOut', models.FloatField(default=0.0)),
                ('amount', models.FloatField(default=0.0)),
                ('time_of_action', models.IntegerField(default=30)),
                ('calc_type', models.CharField(choices=[(b'Df', '\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u0440\u0430\u0441\u0447\u0451\u0442\u043d\u044b\u0439 \u0444\u0443\u043d\u043a\u0446\u0438\u043e\u043d\u0430\u043b'), (b'Dp', '\u041a\u0430\u043a \u0432 IS'), (b'Cp', '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u0441\u043a\u0438\u0439')], default=b'Df', max_length=2)),
            ],
        ),
    ]
