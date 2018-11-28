from django.contrib import admin

from abonapp import models

admin.site.register(models.Abon)
admin.site.register(models.InvoiceForPayment)
admin.site.register(models.AbonLog)
admin.site.register(models.AbonTariff)
admin.site.register(models.AbonStreet)
admin.site.register(models.AbonRawPassword)
admin.site.register(models.PassportInfo)
admin.site.register(models.AdditionalTelephone)
