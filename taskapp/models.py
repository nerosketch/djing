# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db import models
from django.conf import settings

from devapp.models import Device


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


class Task(models.Model):
    descr = models.CharField(max_length=128)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    device = models.ForeignKey(Device, related_name='dev')
    priority = models.CharField(max_length=1, choices=TASK_PRIORITIES, default=TASK_PRIORITIES[2][0])
    out_date = models.DateField(null=True, blank=True, default=datetime.now()+timedelta(days=7))
    time_of_create = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=TASK_STATES, default=TASK_STATES[0][0])

    def __unicode__(self):
        return self.descr

    class Meta:
        db_table = 'task'
        ordering = ('-id',)

    def save_form(self, frm_instance, auth_user):
        cl = frm_instance.cleaned_data
        self.descr = cl['descr']
        self.recipient = cl['recipient']
        self.author = auth_user
        self.device = cl['device']
        self.priority = cl['priority']
        self.out_date = cl['out_date']
        self.state = cl['state']

    def finish(self, current_user):
        self.state = 'F'  # Выполнена
        self.out_date = datetime.now()  # Время завершения

    def begin(self, current_user):
        self.state = 'C'  # Начата
