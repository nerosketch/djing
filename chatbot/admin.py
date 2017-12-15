from django.contrib import admin
from . import models

admin.site.register(models.MessageHistory)
admin.site.register(models.TelegramBot)
admin.site.register(models.MessageQueue)
