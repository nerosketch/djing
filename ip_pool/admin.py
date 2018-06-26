from django.contrib import admin
from ip_pool import models

admin.site.register(models.NetworkModel)
admin.site.register(models.IpLeaseModel)
