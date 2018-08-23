from django.urls import path

from . import views

app_name = 'tariff_app'

urlpatterns = [
    path('', views.TariffsListView.as_view(), name='home'),
    path('<int:tarif_id>/', views.edit_tarif, name='edit'),
    path('add/', views.edit_tarif, name='add'),
    path('del/<int:tid>/', views.TariffDeleteView.as_view(), name='del'),

    path('periodic_pays/', views.PeriodicPaysListView.as_view(), name='periodic_pays'),
    path('periodic_pays/add/', views.periodic_pay, name='periodic_pay_add'),
    path('periodic_pays/<int:pay_id>/', views.periodic_pay, name='periodic_pay_edit')
]
