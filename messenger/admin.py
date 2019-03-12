from django.contrib import admin
from messenger import models

admin.site.register(models.Messenger)
admin.site.register(models.ViberMessenger)
admin.site.register(models.ViberSubscriber)
admin.site.register(models.ViberMessage)
