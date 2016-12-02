# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime, timedelta
import os
from subprocess import call
from django.db import models
from django.conf import settings

from devapp.models import Device
from djing.settings import BASE_DIR


TASK_PRIORITIES = (
    (b'A', u'Высший'),
    (b'B', u'Выше среднего'),
    (b'C', u'Средний'),
    (b'D', u'Ниже среднего'),
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

    def __unicode__(self):
        return self.descr

    class Meta:
        db_table = 'task'
        ordering = ('-id',)

    def finish(self, current_user):
        self.state = 'F'  # Выполнена
        self.out_date = datetime.now()  # Время завершения

    def begin(self, current_user):
        self.state = 'C'  # Начата


def task_handler(sender, instance, **kwargs):
    cur_dir = os.path.join(BASE_DIR, "taskapp")
    if kwargs['created']:
        first_param = 'start'
    else:
        first_param = 'change'
    call(['%s/handle.sh' % cur_dir, first_param, instance.get_mode_display(), instance.device.ip_address,
          instance.state, instance.recipient.telephone, instance.descr])


models.signals.post_save.connect(task_handler, sender=Task)
