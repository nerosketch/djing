# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime, timedelta
#import os
#from subprocess import call
from django.db import models
from django.conf import settings
from abonapp.models import Abon

#from devapp.models import Device
#from djing.settings import BASE_DIR
from handle import handle as task_handle


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


class ChangeLog(models.Model):
    task = models.ForeignKey('Task')
    ACT_CHOICES = (
        (b'e', u'Изменение задачи'),
        (b'c', u'Создание задачи'),
        (b'd', u'Удаление задачи'),
        (b'f', u'Завершение задачи'),
        (b'b', u'Задача начата')
    )
    act_type = models.CharField(max_length=1, choices=ACT_CHOICES)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    def __unicode__(self):
        return self.get_act_type_display()


def _delta_add_days():
    return datetime.now() + timedelta(days=3)

class Task(models.Model):
    descr = models.CharField(max_length=128, null=True, blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='them_task')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    #device = models.ForeignKey(Device, related_name='dev')
    priority = models.CharField(max_length=1, choices=TASK_PRIORITIES, default=TASK_PRIORITIES[2][0])
    out_date = models.DateField(null=True, blank=True, default=_delta_add_days)
    time_of_create = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=TASK_STATES, default=TASK_STATES[0][0])
    attachment = models.ImageField(upload_to='task_attachments/%Y.%m.%d', blank=True, null=True)
    mode = models.CharField(max_length=2, choices=TASK_TYPES, default=TASK_TYPES[0][0])
    abon = models.ForeignKey(Abon, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        db_table = 'task'
        ordering = ('-id',)
        permissions = (
            ('can_viewall', 'Доступ ко всем задачам'),
            ('can_remind', 'Напоминания о задачах')
        )

    def finish(self, current_user):
        self.state = b'F'  # Выполнена
        self.out_date = datetime.now()  # Время завершения
        ChangeLog.objects.create(
            task=self,
            act_type=b'f',
            who=current_user
        )
        self.save(update_fields=['state', 'out_date'])

    def begin(self, current_user):
        self.state = b'C'  # Начата
        ChangeLog.objects.create(
            task=self,
            act_type=b'b',
            who=current_user
        )
        self.save(update_fields=['state'])


def task_handler(sender, instance, **kwargs):
    #cur_dir = os.path.join(BASE_DIR, "taskapp")
    group = ''
    if instance.abon:
        group = instance.abon.group
    if kwargs['created']:
        ChangeLog.objects.create(
            task=instance,
            act_type=b'c',
            who=instance.author
        )
    else:
        ChangeLog.objects.create(
            task=instance,
            act_type=b'e',
            who=instance.author
        )
    for recipient in instance.recipients.all():
        task_handle(
            instance, instance.author,
            recipient, group
        )
        '''
        call(['%s/handle.sh' % cur_dir,
            first_param,                    # start or change
            instance.get_mode_display(),    # mode - Характер поломки
              'N',                          # (ip устройства) Зарезервировано
              instance.state,               # Состояние задачи (новая|выполнена)
              instance.author.telephone,    # Телефон автора задачи
              recipient.telephone,          # Телефон ответственного монтажника
              instance.descr,               # Описание задачи
              # Если указан абонент то инфа о нём
              instance.abon.fio if instance.abon else '<нет фио>',
              instance.abon.address if instance.abon else '<нет адреса>',
              instance.abon.telephone if instance.abon else '<нет телефона>',
              group_name])                  # Имя группы абонента
              '''


def task_delete(sender, instance, **kwargs):
    ChangeLog.objects.create(
        task=instance,
        act_type=b'd',
        who=instance.author
    )


models.signals.post_save.connect(task_handler, sender=Task)
models.signals.post_delete.connect(task_delete, sender=Task)
