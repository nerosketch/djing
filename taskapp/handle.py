# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from djing.tasks import send_email_notify
from chatbot.models import ChatException
from djing.lib import MultipleException


class TaskException(Exception):
    pass


def handle(task, author, recipients):
    errors = []
    for recipient in recipients:
        if not recipient.flags.notify_task:
            continue
        try:
            task_status = _('Task')
            # If signal to myself then quietly
            if author == recipient:
                return
            # If task completed or failed
            elif task.state == 'F' or task.state == 'C':
                task_status = _('Task completed')

            fulltext = render_to_string('taskapp/notification.html', {
                'task': task,
                'abon': task.abon,
                'task_status': task_status
            })

            if task.state == 'F' or task.state == 'C':
                # If task completed or failed than send one message to author
                send_email_notify.delay(fulltext, author.pk)
            else:
                send_email_notify.delay(fulltext, recipient.pk)
        except ChatException as e:
            errors.append(e)
    if len(errors) > 0:
        raise MultipleException(errors)
