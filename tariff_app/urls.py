from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.tarifs, name='tarifs_link'),
    url(r'^(?P<tarif_id>\d+)$', views.edit_tarif, name='tarifs_edit_link'),
    url(r'^add$', views.edit_tarif, name='tarifs_add_link'),
    url(r'^del(?P<id>\d+)$', views.del_tarif, name='tarifs_del_link')
]
