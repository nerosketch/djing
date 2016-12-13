# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime, timedelta
import os
from subprocess import call
from django.db import models
from django.conf import settings
from abonapp.models import Abon

from devapp.models import Device
from djing.settings import BASE_DIR


TASK_PRIORITIES = (
    (b'A', u'Высший'),
    (b'C', u'Средний'),
    (b'E', u'Низкий')
)

TASK_STATES = (
    (b'S', u'Новая'),
    (b'C', u'На выполнении'),
    (b'F', u'Выполнена')
)

TASK_TYPES = (
    (b'na', u'не выбрано'),
    (b'yt', u'жёлтый треугольник'),
    (b'rc', u'красный крестик'),
    (b'ls', u'слабая скорость'),
    (b'cf', u'обрыв кабеля'),
    (b'cn', u'подключение'),
    (b'pf', u'переодическое пропадание'),
    (b'cr', u'настройка роутера'),
    (b'co', u'настроить onu'),
    (b'fc', u'обжать кабель'),
    (b'ot', u'другое')
)


class Task(models.Model):
    descr = models.CharField(max_length=128)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    device = models.ForeignKey(Device, related_name='dev')
    priority = models.CharField(max_length=1, choices=TASK_PRIORITIES, default=TASK_PRIORITIES[2][0])
    out_date = models.DateField(null=True, blank=True, default=datetime.now() + timedelta(days=7))
    time_of_create = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=TASK_STATES, default=TASK_STATES[0][0])
    attachment = models.ImageField(upload_to='task_attachments/%Y.%m.%d', blank=True, null=True)
    mode = models.CharField(max_length=2, choices=TASK_TYPES, default=TASK_TYPES[0][0])
    abon = models.ForeignKey(Abon, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __unicode__(self):
        return self.descr

    class Meta:
        db_table = 'task'
        ordering = ('-id',)
        permissions = (
            ('can_viewall', 'Доступ ко всем задачам'),
        )

    def finish(self, current_user):
        self.state = 'F'  # Выполнена
        self.out_date = datetime.now()  # Время завершения

    def begin(self, current_user):
        self.state = 'C'  # Начата


class ChangeLog(models.Model):
    task = models.ForeignKey(Task)
    ACT_CHOICES = (
        (b'e', u'Изменение задачи'),
        (b'c', u'Создание задачи'),
        (b'd', u'Удаление задачи')
    )
    act_type = models.CharField(max_length=1, choices=ACT_CHOICES)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    def __unicode__(self):
        return self.get_act_type_display()


def task_handler(sender, instance, **kwargs):
    cur_dir = os.path.join(BASE_DIR, "taskapp")
    group_name = ''
    if instance.abon:
        if instance.abon.group:
            group_name = instance.abon.group.title
    if kwargs['created']:
        first_param = 'start'
        ChangeLog.objects.create(
            task=instance,
            act_type=b'c',
            who=instance.author
        )
    else:
        first_param = 'change'
        ChangeLog.objects.create(
            task=instance,
            act_type=b'e',
            who=instance.author
        )
    call(['%s/handle.sh' % cur_dir,
        first_param,                    # start or change
        instance.get_mode_display(),    # mode - Характер поломки
          instance.device.ip_address,   # ip устройства
          instance.state,               # Состояние задачи (новая|выполнена)
          instance.author.telephone,    # Телефон автора задачи
          instance.recipient.telephone, # Телефон ответственного монтажника
          instance.descr,               # Описание задачи
          # Если указан абонент то инфа о нём
          instance.abon.fio if instance.abon else '<нет фио>',
          instance.abon.address if instance.abon else '<нет адреса>',
          instance.abon.telephone if instance.abon else '<нет телефона>',
          group_name])                  # Имя группы абонента


models.signals.post_save.connect(task_handler, sender=Task)
