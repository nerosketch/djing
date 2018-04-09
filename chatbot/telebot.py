# -*- coding: utf-8 -*-
from telepot import helper, glance, Bot
from telepot.exception import TelegramError
import os
import socket
import collections
from django.utils.translation import ugettext as _
from urllib3.exceptions import ProtocolError
from .models import TelegramBot, ChatException, MessageQueue
from chatbot.models import MessageHistory
from accounts_app.models import UserProfile
from django.conf import settings

token = getattr(settings, 'TELEGRAM_BOT_TOKEN')


class DjingTelebot(helper.ChatHandler):
    _current_user = None
    _dialog_fn = None
    _chat_id = 0

    def __init__(self, seed_tuple, **kwargs):
        super(DjingTelebot, self).__init__(seed_tuple, **kwargs)
        self.cmds = {
            'ping': self.ping,
            'iam': self.say_me
        }

    # отвечаем пользователю
    def _sent_reply(self, text):
        self.sender.sendMessage(text)

    # задаём вопрос пользователю, и ожидаем ответ в fn
    def _question(self, text, fn):
        if not isinstance(fn, collections.Callable):
            raise TypeError
        self._dialog_fn = fn
        if text is not None:
            self._sent_reply(text)

    # сохраняем сообщение в базе
    def _message_log(self, msg):
        if self._current_user is None:
            self._question(None, self.question_name)
            return False
        MessageHistory.objects.create(
            user=self._current_user,
            message=msg
        )
        return True

    # Начинаем диалог
    # @seed - chat_id
    def open(self, initial_msg, seed):
        content_type, chat_type, chat_id = glance(initial_msg)
        if content_type != 'text':
            return True
        self._chat_id = chat_id
        try:
            tbot = TelegramBot.objects.get(chat_id=seed)
            self._current_user = tbot.user
            self._message_log(initial_msg['text'])
        except TelegramBot.DoesNotExist:
            self._question(_("Let's get acquainted, what is your name? Write your login from billing."),
                           self.question_name)
        return True  # prevent on_message() from being called on the initial message

    # получаем сообщение
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = glance(msg)
        if content_type != 'text':
            return
        self._chat_id = chat_id
        text = msg['text'].lower()

        # выполняем комманды если они есть
        if text in list(self.cmds.keys()):
            self.cmds[text]()
        elif self._dialog_fn is not None:
            if not callable(self._dialog_fn):
                raise TypeError
            self._dialog_fn(text)
            self._dialog_fn = None
        else:
            self._sent_reply(_('I do not know the answer to this yet.'))

        if not self._message_log(text):
            return

    # спрашиваем имя пользователя
    def question_name(self, username):
        try:
            profile = UserProfile.objects.get(username=username)
            self._current_user = profile
            try:
                TelegramBot.objects.get(user=profile)
            except TelegramBot.DoesNotExist:
                if self._chat_id == 0:
                    raise ChatException('telebot.py. def question_name: Chat id is empty')
                TelegramBot.objects.create(
                    user=profile,
                    chat_id=self._chat_id
                )
        except UserProfile.DoesNotExist:
            self._question(
                _("You are not found in the database, check that it correctly pointed out its LOGIN. Try again"),
                self.question_name)
            return
        self._sent_reply(
            _("Yes, it's nice to meet %(username)s, I will notify you about events in billing. Successful work ;)")
            % {'username': profile.get_full_name()})

    # заканчивается время диалога
    # ex - время ожидания (timeout=ex в pave_event_space)
    def on_close(self, ex):
        self._current_user = None
        self._dialog_fn = None
        self._chat_id = 0

    def ping(self, ip=None):
        if ip is None:
            self._question(_("Let's ping, write ip. It will be necessary to wait 10 seconds"), self.ping)
            return
        try:
            socket.inet_aton(ip)
            ret = os.popen('`which ping` -c 10 ' + ip).read()
            self._sent_reply(ret)
        except socket.error:
            self._question(_("It's not like ip address, try again"), self.ping)

    def say_me(self):
        self._sent_reply(_("You're '%s', right?") % self._current_user.get_full_name())


# Just sending text to specified account
def send_notify(msg_text, account, tag='none'):
    try:
        MessageQueue.objects.push(msg=msg_text, user=account, tag=tag)
        if token is None:
            raise ChatException(_('Telegram bot token not found'))
        tb = TelegramBot.objects.get(user=account)
        tbot = Bot(token)
        tbot.sendMessage(tb.chat_id, msg_text)
    except TelegramBot.DoesNotExist:
        raise ChatException(_("Recipient '%s' does not subscribed on notifications") % account.get_full_name())
    except ProtocolError as e:
        raise ChatException('ProtocolError: %s' % e)
    except TelegramError as e:
        raise ChatException('Telegram error: %s' % e)
