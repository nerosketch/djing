from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.peoples, name='people_list_link'),
    url(r'^addabon$', views.addabon, name='addabon_link'),
    url(r'^(?P<uid>\d+)$', views.abonhome, name='abonhome_link'),

    url(r'^(?P<uid>\d+)/services$', views.abon_services, name='abon_services_link'),
    url(r'^(?P<uid>\d+)/amount', views.abonamount, name='abon_amount_link'),
    url(r'^(?P<uid>\d+)/debts', views.invoice_for_payment, name='abon_debts_link'),
    url(r'^(?P<uid>\d+)/pay_history', views.pay_history, name='abon_phistory_link'),


    url(r'^(?P<uid>\d+)/addinvoice$', views.add_invoice, name='abonapp_addinvoice_link'),
    url(r'^(?P<uid>\d+)/buy$', views.buy_tariff, name='abonapp_buy_tariff'),
    url(r'^(?P<uid>\d+)/chpriority$', views.chpriority, name='abonapp_chpriority_tariff'),
    url(r'^(?P<uid>\d+)/complete_service(?P<srvid>\d+)$', views.complete_service, name='abonapp_compl_srv'),
    url(r'^(?P<uid>\d+)/activate_service(?P<srvid>\d+)$', views.activate_service, name='abonapp_activate_service'),

    url(r'^(?P<uid>\d+)/unsubscribe_service(?P<srvid>\d+)$', views.unsubscribe_service, name='abonapp_unsubscribe_service')
]
