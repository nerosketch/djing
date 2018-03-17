# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _
from chatbot.telebot import send_notify
from chatbot.models import ChatException
from mydefs import MultipleException


class TaskException(Exception):
    pass


def handle(task, author, recipients, abon_group):
    errors = []
    for recipient in recipients:
        try:
            dst_account = recipient
            text = _('Task')
            # If signal to myself then quietly
            if author == recipient:
                return
            # If task completed or failed
            elif task.state == 'F' or task.state == 'C':
                text = _('Task completed')
            if task.abon is not None:
                fulltext = "%s:\n%s\n" % (text, task.abon.get_full_name())
            else:
                fulltext = "%s\n" % text
            fulltext += _('locality %s.\n') % abon_group.title
            if task.abon:
                fulltext += _('address %(street)s %(house)s.\ntelephone %(telephone)s\n') % {
                    'street': task.abon.street.name if task.abon.street is not None else '<'+_('not chosen')+'>',
                    'house': task.abon.house,
                    'telephone': task.abon.telephone
                }
            fulltext += _('Task type - %s.') % task.get_mode_display() + '\n'
            fulltext += task.descr if task.descr else ''

            if task.state == 'F' or task.state == 'C':
                # If task completed or failed than send one message to author
                try:
                    send_notify(fulltext, author, tag='taskap')
                except ChatException as e:
                    raise TaskException(e)
            else:
                send_notify(fulltext, dst_account, tag='taskap')
        except ChatException as e:
            errors.append(e)
    if len(errors) > 0:
        raise MultipleException(errors)
