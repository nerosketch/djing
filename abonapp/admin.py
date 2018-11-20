from django.contrib import admin

from abonapp.models import generic

admin.site.register(generic.Abon)
admin.site.register(generic.InvoiceForPayment)
admin.site.register(generic.AbonLog)
admin.site.register(generic.AbonTariff)
admin.site.register(generic.AbonStreet)
admin.site.register(generic.AllTimePayLog)
admin.site.register(generic.AbonRawPassword)
admin.site.register(generic.PassportInfo)
admin.site.register(generic.AdditionalTelephone)
