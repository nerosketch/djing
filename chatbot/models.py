from django.db import models
from djing.settings import AUTH_USER_MODEL


class TelegramBot(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL)
    chat_id = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return self.user.get_full_name() + ' - ' + str(self.chat_id)


class MessageHistory(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL)
    message = models.CharField(max_length=255)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.message
