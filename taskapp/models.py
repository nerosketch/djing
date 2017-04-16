# coding=utf-8
from datetime import timedelta
import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from abonapp.models import Abon
from .handle import handle as task_handle, TaskException
from mydefs import MultipleException


TASK_PRIORITIES = (
    ('A', _('Higher')),
    ('C', _('Average')),
    ('E', _('Low'))
)

TASK_STATES = (
    ('S', _('New')),
    ('C', _('In fulfilling')),
    ('F', _('Completed'))
)

TASK_TYPES = (
    ('na', _('not chosen')),
    ('yt', _('yellow triangle')),
    ('rc', _('red cross')),
    ('ls', _('weak speed')),
    ('cf', _('cable break')),
    ('cn', _('connection')),
    ('pf', _('periodic disappearance')),
    ('cr', _('router setup')),
    ('co', _('configure onu')),
    ('fc', _('crimp cable')),
    ('ot', _('other'))
)


class ChangeLog(models.Model):
    task = models.ForeignKey('Task')
    ACT_CHOICES = (
        ('e', _('Change task')),
        ('c', _('Create task')),
        ('d', _('Delete task')),
        ('f', _('Completing tasks')),
        ('b', _('The task started'))
    )
    act_type = models.CharField(max_length=1, choices=ACT_CHOICES)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

    def __str__(self):
        return self.get_act_type_display()


def _delta_add_days():
    return timezone.now() + timedelta(days=3)


class Task(models.Model):
    descr = models.CharField(max_length=128, null=True, blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='them_task')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)
    #device = models.ForeignKey(Device, related_name='dev')
    priority = models.CharField(max_length=1, choices=TASK_PRIORITIES, default=TASK_PRIORITIES[2][0])
    out_date = models.DateField(null=True, blank=True, default=_delta_add_days)
    time_of_create = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=TASK_STATES, default=TASK_STATES[0][0])
    attachment = models.ImageField(upload_to='task_attachments/%Y.%m.%d', blank=True, null=True)
    mode = models.CharField(max_length=2, choices=TASK_TYPES, default=TASK_TYPES[0][0])
    abon = models.ForeignKey(Abon, null=True, blank=True)

    class Meta:
        db_table = 'task'
        ordering = ('-id',)
        permissions = (
            ('can_viewall', _('Access to all tasks')),
            ('can_remind', _('Reminders of tasks'))
        )

    def finish(self, current_user):
        self.state = 'F'  # Выполнена
        self.out_date = timezone.now()  # Время завершения
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

    def get_attachment_fname(self):
        return os.path.basename(self.attachment.name)

    def is_outdated(self):
        return self.out_date < timezone.now().date()


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
    errors = []
    for recipient in instance.recipients.all():
        try:
            task_handle(
                instance, instance.author,
                recipient, group
            )
        except TaskException as e:
            errors.append(e)
    if len(errors) > 0:
        raise MultipleException(errors)


#def task_delete(sender, instance, **kwargs):
#    ChangeLog.objects.create(
#        task=instance,
#        act_type='d',
#        who=instance.author
#    )


models.signals.post_save.connect(task_handler, sender=Task)
#models.signals.post_delete.connect(task_delete, sender=Task)
