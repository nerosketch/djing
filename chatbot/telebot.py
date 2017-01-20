# -*- coding: utf-8 -*-
from telepot import helper, glance, Bot
import os
import socket
from .models import TelegramBot, ChatException
from chatbot.models import MessageHistory
from accounts_app.models import UserProfile
import collections

token = '285129725:AAF9Si5_b1n1_cN3vJtwXt0gkgsqKBptut4'


class DjingTelebot(helper.ChatHandler):
    _current_user = None
    _dialog_fn = None
    _chat_id = 0

    def __init__(self, seed_tuple, **kwargs):
        super().__init__(seed_tuple, **kwargs)
        self.cmds = {
            'ping': self.ping,
            'iam': self.say_me
        }

    # отвечаем пользователю
    def _sent_reply(self, text):
        self.sender.sendMessage(text)

    # задаём вопрос пользователю, и ожидаем ответ в fn
    def _question(self, text, fn):
        assert isinstance(fn, collections.Callable)
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
            self._question('Давай знакомиться, как тебя зовут? Напиши свой логин из биллинга.',
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
            assert callable(self._dialog_fn)
            self._dialog_fn(text)
            self._dialog_fn = None
        else:
            self._sent_reply('Я пока не знаю ответа на это')

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
                assert self._chat_id != 0
                TelegramBot.objects.create(
                    user=profile,
                    chat_id=self._chat_id
                )
        except UserProfile.DoesNotExist:
            self._question('Ты не найден в базе, проверь что правильно указал именно свой ЛОГИН. Попробуй ещё',
                           self.question_name)
            return
        self._sent_reply('Да, приятно познакомиться %s, я буду оповещать тебя о событиях в биллинге. Удачной работы ;)'
                         % profile.get_full_name())

    # заканчивается время диалога
    # ex - время ожидания (timeout=ex в pave_event_space)
    def on_close(self, ex):
        self._current_user = None
        self._dialog_fn = None
        self._chat_id = 0

    # пингуем адрес
    def ping(self, ip=None):
        if ip is None:
            self._question('Давай пинганём, напиши ip. Нужно будет подождать 10 сек', self.ping)
            return
        try:
            socket.inet_aton(ip)
            ret = os.popen('`which ping` -c 10 ' + ip).read()
            self._sent_reply(ret)
        except socket.error:
            self._question('Это не похоже на ip адрес, попробуй ещё', self.ping)

    def say_me(self):
        self._sent_reply('Ты ведь %s ?' % self._current_user.get_full_name())


# Просто отправляем текст оповещения указанному админу
def send_notify(msg_text, account):
    print(account)
    try:
        tb = TelegramBot.objects.get(user=account)
        tbot = Bot(token)
        tbot.sendMessage(tb.chat_id, msg_text)
    except TelegramBot.DoesNotExist:
        raise ChatException('Цель оповещения не подписан на оповещения')
