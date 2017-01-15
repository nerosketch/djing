# -*- coding: utf-8 -*-
from chatbot.telebot import send_notify


def handle(task, author, recipient, abon_group):
    print author, recipient
    dst_account = recipient
    text = u'Задача'
    # Если сигнал самому себе то молчим
    if author == recipient:
        return
    # Если задача 'На выполнении' то молчим
    if task.state == b'C':
        return
    # Если задача завершена
    elif task.state == b'F':
        text = u'Задача завершена'
        # Меняем телефон назначения на телефон автора, т.к. при завершении
        # идёт оповещение автору о выполнении
        dst_account = author
    fulltext=u"%s: %s. " % (text, task.abon.get_full_name())
    if task.abon:
        fulltext += u"по адресу %s тел. %s. " % (
            task.abon.address, task.abon.telephone
        )
    fulltext += u"с. %s. Тип задачи - %s. " % (abon_group.title, task.get_mode_display())
    fulltext += task.descr if task.descr else u'<без описания>'
    send_notify(fulltext, dst_account)
