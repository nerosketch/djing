from django.contrib import admin

from . import models


admin.site.register(models.AbonGroup)
admin.site.register(models.Abon)
admin.site.register(models.InvoiceForPayment)
admin.site.register(models.AbonLog)
admin.site.register(models.AbonTariff)
admin.site.register(models.AbonStreets)
