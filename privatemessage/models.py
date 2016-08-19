from django.db import models
from djing import settings


class MessagesManager(models.Manager):

    def get_my_messages(self, request):
        if request.user.is_authenticated():
            num = self.filter(recepient=request.user, is_viewed=False).count()
        else:
            num = 0
        return int(num)


class Dialog(models.Model):
    title = models.CharField(max_length=127)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    recepient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    date_create = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title


class PrivateMessages(models.Model):
    dialog = models.ForeignKey(Dialog)
    date_send = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    is_viewed = models.BooleanField(default=False)

    objects = MessagesManager()

    def __unicode__(self):
        return self.text
