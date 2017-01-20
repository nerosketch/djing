# coding=utf-8
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from abonapp.models import Abon
from .handle import handle as task_handle


TASK_PRIORITIES = (
    ('A', 'Высший'),
    ('C', 'Средний'),
    ('E', 'Низкий')
)

TASK_STATES = (
    ('S', 'Новая'),
    ('C', 'На выполнении'),
    ('F', 'Выполнена')
)

TASK_TYPES = (
    ('na', 'не выбрано'),
    ('yt', 'жёлтый треугольник'),
    ('rc', 'красный крестик'),
    ('ls', 'слабая скорость'),
    ('cf', 'обрыв кабеля'),
    ('cn', 'подключение'),
    ('pf', 'переодическое пропадание'),
    ('cr', 'настройка роутера'),
    ('co', 'настроить onu'),
    ('fc', 'обжать кабель'),
    ('ot', 'другое')
)


class ChangeLog(models.Model):
    task = models.ForeignKey('Task')
    ACT_CHOICES = (
        ('e', 'Изменение задачи'),
        ('c', 'Создание задачи'),
        ('d', 'Удаление задачи'),
        ('f', 'Завершение задачи'),
        ('b', 'Задача начата')
    )
    act_type = models.CharField(max_length=1, choices=ACT_CHOICES)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    def __str__(self):
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
        self.state = 'F'  # Выполнена
        self.out_date = datetime.now()  # Время завершения
        ChangeLog.objects.create(
            task=self,
            act_type='f',
            who=current_user
        )
        self.save(update_fields=['state', 'out_date'])

    def begin(self, current_user):
        self.state = 'C'  # Начата
        ChangeLog.objects.create(
            task=self,
            act_type='b',
            who=current_user
        )
        self.save(update_fields=['state'])


def task_handler(sender, instance, **kwargs):
    group = ''
    if instance.abon:
        group = instance.abon.group
    if kwargs['created']:
        ChangeLog.objects.create(
            task=instance,
            act_type='c',
            who=instance.author
        )
    else:
        ChangeLog.objects.create(
            task=instance,
            act_type='e',
            who=instance.author
        )
    for recipient in instance.recipients.all():
        task_handle(
            instance, instance.author,
            recipient, group
        )


def task_delete(sender, instance, **kwargs):
    ChangeLog.objects.create(
        task=instance,
        act_type='d',
        who=instance.author
    )


models.signals.post_save.connect(task_handler, sender=Task)
models.signals.post_delete.connect(task_delete, sender=Task)
