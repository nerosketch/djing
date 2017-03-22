# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from chatbot.telebot import send_notify
from chatbot.models import ChatException


class TaskException(Exception):
    pass


def handle(task, author, recipient, abon_group):
    try:
        dst_account = recipient
        text = _('Task')
        # Если сигнал самому себе то молчим
        if author == recipient:
            return
        # Если задача 'На выполнении' то молчим
        if task.state == 'C':
            return
        # Если задача завершена
        elif task.state == 'F':
            text = _('Task completed')
            # Меняем цель назначения на автора, т.к. при завершении
            # идёт оповещение автору о выполнении
            dst_account = author
        if task.abon is not None:
            fulltext="%s:\n%s\n" % (text, task.abon.get_full_name())
        else:
            fulltext="%s\n" % text
        fulltext += _('locality %s.\n') % abon_group.title
        if task.abon:
            fulltext += _('address %s %s.\ntelephone %s\n') % (
                task.abon.street.name if task.abon.street is not None else '<'+_('not chosen')+'>',
                task.abon.house,
                task.abon.telephone
            )
        fulltext += _('Task type - %s.\n') % task.get_mode_display()
        fulltext += task.descr if task.descr else ''
        send_notify(fulltext, dst_account)
    except ChatException as e:
        raise TaskException(e)
