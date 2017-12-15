#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
from pid.decorator import pidfile
import django
from telepot import DelegatorBot
from telepot.delegate import per_chat_id, create_open, pave_event_space


@pidfile(pidname='djing_telebot.pid', piddir='/run')
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from chatbot.telebot import token, DjingTelebot
    bot = DelegatorBot(token, [
        pave_event_space()(
            per_chat_id(), create_open, DjingTelebot, timeout=300
        ),
    ])
    bot.message_loop(run_forever='Listening ...')


if __name__ == '__main__':
    main()
