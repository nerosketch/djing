#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import django
from telepot import DelegatorBot
from telepot.delegate import per_chat_id, create_open, pave_event_space


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from chatbot.telebot import token, DjingTelebot
    bot = DelegatorBot(token, [
        pave_event_space()(
            per_chat_id(), create_open, DjingTelebot, timeout=300
        ),
    ])
    bot.message_loop(run_forever='Listening ...')
