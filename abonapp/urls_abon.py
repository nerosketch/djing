from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.peoples, name='people_list'),
    url(r'^addabon$', views.addabon, name='add_abon'),
    url(r'^services$', views.chgroup_tariff, name='ch_group_tariff'),
    url(r'^(?P<uid>\d+)$', views.abonhome, name='abon_home'),

    url(r'^(?P<uid>\d+)/services$', views.abon_services, name='abon_services'),
    url(r'^(?P<uid>\d+)/amount', views.abonamount, name='abon_amount'),
    url(r'^(?P<uid>\d+)/debts', views.invoice_for_payment, name='abon_debts'),
    url(r'^(?P<uid>\d+)/pay', views.pay_history, name='abon_phistory'),

    url(r'^(?P<uid>\d+)/addinvoice$', views.add_invoice, name='add_invoice'),
    url(r'^(?P<uid>\d+)/pick$', views.pick_tariff, name='pick_tariff'),
    url(r'^(?P<uid>\d+)/passport_view$', views.passport_view, name='passport_view'),
    url(r'^(?P<uid>\d+)/complete_service(?P<srvid>\d+)$', views.complete_service, name='compl_srv'),
    url(r'^(?P<uid>\d+)/opt82$', views.opt82, name='opt82'),
    url(r'^(?P<uid>\d+)/chart$', views.charts, name='charts'),
    url(r'^(?P<uid>\d+)/dials$', views.dials, name='dials'),
    url(r'^(?P<uid>\d+)/extra_field$', views.make_extra_field, name='extra_field'),
    url(r'^(?P<uid>\d+)/extra_field/(?P<fid>\d+)/delete$', views.extra_field_delete, name='extra_field_delete'),
    url(r'^(?P<uid>\d+)/extra_field/edit$', views.extra_field_change, name='extra_field_edit'),

    url(r'^(?P<uid>\d+)/unsubscribe_service(?P<srvid>\d+)$', views.unsubscribe_service,
        name='unsubscribe_service'),

    url(r'^(?P<uid>\d+)/dev/$', views.dev, name='dev'),
    url(r'^(?P<uid>\d+)/clear_dev/$', views.clear_dev, name='clear_dev'),

    url(r'^(?P<uid>\d+)/task_log$', views.task_log, name='task_log')
]
