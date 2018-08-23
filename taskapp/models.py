# coding=utf-8
from datetime import timedelta
import os
from django.db import models
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.translation import ugettext as _
from abonapp.models import Abon
from .handle import handle as task_handle

TASK_PRIORITIES = (
    ('A', _('Higher')),
    ('C', _('Average')),
    ('E', _('Low'))
)

TASK_STATES = (
    ('S', _('New')),
    ('C', _('Confused')),
    ('F', _('Completed'))
)

TASK_TYPES = (
    ('na', _('not chosen')),
    ('ic', _('ip conflict')),
    ('yt', _('yellow triangle')),
    ('rc', _('red cross')),
    ('ls', _('weak speed')),
    ('cf', _('cable break')),
    ('cn', _('connection')),
    ('pf', _('periodic disappearance')),
    ('cr', _('router setup')),
    ('co', _('configure onu')),
    ('fc', _('crimp cable')),
    ('ni', _('Internet crash')),
    ('ot', _('other'))
)


class ChangeLog(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    ACT_CHOICES = (
        ('e', _('Change task')),
        ('c', _('Create task')),
        ('d', _('Delete task')),
        ('f', _('Completing tasks')),
        ('b', _('The task failed'))
    )
    act_type = models.CharField(max_length=1, choices=ACT_CHOICES)
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')

    def __str__(self):
        return self.get_act_type_display()


def delta_add_days():
    return timezone.now() + timedelta(days=3)


class Task(models.Model):
    descr = models.CharField(_('Description'), max_length=128, null=True, blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Recipients'),
                                        related_name='them_task')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.SET_NULL, null=True,
                               blank=True, verbose_name=_('Task author'))
    priority = models.CharField(_('A priority'), max_length=1, choices=TASK_PRIORITIES, default=TASK_PRIORITIES[2][0])
    out_date = models.DateField(_('Reality'), null=True, blank=True, default=delta_add_days)
    time_of_create = models.DateTimeField(_('Date of create'), auto_now_add=True)
    state = models.CharField(_('Condition'), max_length=1, choices=TASK_STATES, default=TASK_STATES[0][0])
    attachment = models.ImageField(_('Attached image'), upload_to='task_attachments/%Y.%m.%d', blank=True, null=True)
    mode = models.CharField(_('The nature of the damage'), max_length=2, choices=TASK_TYPES, default=TASK_TYPES[0][0])
    abon = models.ForeignKey(Abon, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Subscriber'))

    class Meta:
        db_table = 'task'
        ordering = ('-id',)
        permissions = (
            ('can_viewall', _('Access to all tasks')),
            ('can_remind', _('Reminders of tasks'))
        )

    def finish(self, current_user):
        self.state = 'F'  # Finished
        self.out_date = timezone.now()  # End time
        ChangeLog.objects.create(
            task=self,
            act_type='f',
            who=current_user
        )
        self.save(update_fields=('state', 'out_date'))

    def do_fail(self, current_user):
        self.state = 'C'  # Crashed
        ChangeLog.objects.create(
            task=self,
            act_type='b',
            who=current_user
        )
        self.save(update_fields=('state',))

    def send_notification(self):
        if self.abon:
           group = self.abon.group
        else:
           group = ''
        task_handle(
           self, self.author,
           self.recipients.all(), group
        )

    def get_attachment_fname(self):
        return os.path.basename(self.attachment.name)

    def is_relevant(self):
        return self.out_date < timezone.now().date() or self.state == 'F'


class ExtraComment(models.Model):
    text = models.TextField(_('Text of comment'))
    task = models.ForeignKey(Task, verbose_name=_('Owner task'), on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Author'), on_delete=models.CASCADE)
    date_create = models.DateTimeField(_('Time of create'), auto_now_add=True)

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return resolve_url('taskapp:edit', self.task.pk)

    class Meta:
        db_table = 'extra_comments'
        permissions = (
            ('can_view_comments', _('Can view comments')),
        )
        verbose_name = _('Extra comment')
        verbose_name_plural = _('Extra comments')
        ordering = ('-date_create',)
