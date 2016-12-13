from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.tarifs, name='home'),
    url(r'^(?P<tarif_id>\d+)$', views.edit_tarif, name='edit'),
    url(r'^add$', views.edit_tarif, name='add'),
    url(r'^del(?P<id>\d+)$', views.del_tarif, name='del')
]
