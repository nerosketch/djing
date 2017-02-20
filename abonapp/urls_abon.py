from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.peoples, name='people_list'),
    url(r'^addabon$', views.addabon, name='add_abon'),
    url(r'^(?P<uid>\d+)$', views.abonhome, name='abon_home'),

    url(r'^(?P<uid>\d+)/services$', views.abon_services, name='abon_services'),
    url(r'^(?P<uid>\d+)/amount', views.abonamount, name='abon_amount'),
    url(r'^(?P<uid>\d+)/debts', views.invoice_for_payment, name='abon_debts'),
    url(r'^(?P<uid>\d+)/pay_history', views.pay_history, name='abon_phistory'),

    url(r'^(?P<uid>\d+)/addinvoice$', views.add_invoice, name='add_invoice'),
    url(r'^(?P<uid>\d+)/pick$', views.pick_tariff, name='pick_tariff'),
    url(r'^(?P<uid>\d+)/chpriority$', views.chpriority, name='chpriority_tariff'),
    url(r'^(?P<uid>\d+)/passport_view$', views.passport_view, name='passport_view'),
    url(r'^(?P<uid>\d+)/complete_service(?P<srvid>\d+)$', views.complete_service, name='compl_srv'),
    url(r'^(?P<uid>\d+)/activate_service(?P<srvid>\d+)$', views.activate_service, name='activate_service'),

    url(r'^(?P<uid>\d+)/unsubscribe_service(?P<srvid>\d+)$', views.unsubscribe_service,
        name='unsubscribe_service'),

    url(r'^(?P<uid>\d+)/task_log$', views.task_log, name='task_log')
]
