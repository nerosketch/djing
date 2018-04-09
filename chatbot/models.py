from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class ChatException(Exception):
    pass


class TelegramBot(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, models.CASCADE, verbose_name=_('Employee'))
    chat_id = models.PositiveIntegerField(_('Telegram chat id'), default=0)

    def __str__(self):
        return "%s - %d" % (self.user.get_full_name(), self.chat_id)

    class Meta:
        db_table = 'chat_telegram_bot'
        verbose_name = _('Telegram bot')
        verbose_name_plural = _('Telegram bots')


class MessageHistory(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, models.CASCADE)
    message = models.CharField(max_length=255)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        db_table = 'chat_message_history'
        verbose_name = _('Message history')
        verbose_name_plural = _('Message histories')


class MessageQueueManager(models.Manager):
    def pop(self, user, tag='none'):
        msgs = self.filter(target_employee=user, status='n', tag=tag)[:1].only('message').values('id', 'message')
        if len(msgs) > 0:
            self.filter(id=msgs[0]['id']).delete()
            return msgs[0]['message']

    def push(self, msg, user, tag='none'):
        msg = self.create(target_employee=user, message=msg, tag=tag)
        return msg


class MessageQueue(models.Model):
    target_employee = models.ForeignKey(AUTH_USER_MODEL, models.CASCADE, verbose_name=_('Target employee'))
    message = models.CharField(_('Message'), max_length=255)
    STATUSES = (
        ('n', 'New'),
        ('r', 'Read')
    )
    status = models.CharField(_('Status of message'), max_length=1, choices=STATUSES, default='n')
    # tag: each application puts its own to separate messages between these applications
    tag = models.CharField(_('App tag'), max_length=6, default='none')

    objects = MessageQueueManager()

    def __str__(self):
        return self.message

    class Meta:
        db_table = 'chat_message_queue'
        verbose_name = _('Message queue')
        verbose_name_plural = _('Message queue')
