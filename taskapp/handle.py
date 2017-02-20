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
            # Меняем телефон назначения на телефон автора, т.к. при завершении
            # идёт оповещение автору о выполнении
            dst_account = author
        fulltext="%s: %s. " % (text, task.abon.get_full_name())
        if task.abon:
            fulltext += _('address %s. telephone %s. ') % (
                task.abon.address, task.abon.telephone
            )
        fulltext += _('locality %s. Task type - %s. ') % (abon_group.title, task.get_mode_display())
        fulltext += task.descr if task.descr else _('Not assigned')
        send_notify(fulltext, dst_account)
    except ChatException as e:
        raise TaskException(e)
