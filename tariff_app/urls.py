from django.conf.urls import url

from . import views

app_name = 'tariff_app'

urlpatterns = [
    url(r'^$', views.TariffsListView.as_view(), name='home'),
    url(r'^(?P<tarif_id>\d+)$', views.edit_tarif, name='edit'),
    url(r'^add$', views.edit_tarif, name='add'),
    url(r'^del(?P<tid>\d+)$', views.del_tarif, name='del'),

    url(r'^periodic_pays$', views.periodic_pays, name='periodic_pays'),
    url(r'^periodic_pays/add$', views.periodic_pay, name='periodic_pay_add'),
    url(r'^periodic_pays/(?P<pay_id>\d+)$', views.periodic_pay, name='periodic_pay_edit')
]
