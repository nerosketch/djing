from django.conf.urls import url

from . import views

app_name = 'tariff_app'

urlpatterns = [
    url(r'^$', views.tarifs, name='home'),
    url(r'^(?P<tarif_id>\d+)$', views.edit_tarif, name='edit'),
    url(r'^add$', views.edit_tarif, name='add'),
    url(r'^del(?P<tid>\d+)$', views.del_tarif, name='del')
]
