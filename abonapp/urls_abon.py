from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.peoples, name='people_list'),
    url(r'^addabon$', views.addabon, name='add_abon'),
    url(r'^services$', views.chgroup_tariff, name='ch_group_tariff'),
    url(r'^phonebook$', views.phonebook, name='phonebook'),
    url(r'^export$', views.abon_export, name='abon_export'),
    url(r'^street/add$', views.street_add, name='street_add'),
    url(r'^street/edit', views.street_edit, name='street_edit'),
    url(r'^street/(?P<sid>\d+)/delete$', views.street_del, name='street_del'),
    url(r'^(?P<uid>\d+)$', views.abonhome, name='abon_home'),

    url(r'^(?P<uid>\d+)/services$', views.abon_services, name='abon_services'),
    url(r'^(?P<uid>\d+)/amount', views.abonamount, name='abon_amount'),
    url(r'^(?P<uid>\d+)/debts', views.invoice_for_payment, name='abon_debts'),
    url(r'^(?P<uid>\d+)/pay', views.pay_history, name='abon_phistory'),

    url(r'^(?P<uid>\d+)/addinvoice$', views.add_invoice, name='add_invoice'),
    url(r'^(?P<uid>\d+)/pick$', views.pick_tariff, name='pick_tariff'),
    url(r'^(?P<uid>\d+)/passport_view$', views.passport_view, name='passport_view'),
    url(r'^(?P<uid>\d+)/chart$', views.charts, name='charts'),
    url(r'^(?P<uid>\d+)/dials$', views.dials, name='dials'),
    url(r'^(?P<uid>\d+)/reset_ip$', views.reset_ip, name='reset_ip'),
    url(r'^(?P<uid>\d+)/extra_field$', views.make_extra_field, name='extra_field'),
    url(r'^(?P<uid>\d+)/extra_field/(?P<fid>\d+)/delete$', views.extra_field_delete, name='extra_field_delete'),
    url(r'^(?P<uid>\d+)/extra_field/edit$', views.extra_field_change, name='extra_field_edit'),

    url(r'^(?P<uid>\d+)/unsubscribe_service(?P<abon_tariff_id>\d+)$', views.unsubscribe_service,
        name='unsubscribe_service'),

    url(r'^(?P<uid>\d+)/dev/$', views.dev, name='dev'),
    url(r'^(?P<uid>\d+)/clear_dev/$', views.clear_dev, name='clear_dev'),

    url(r'^(?P<uid>\d+)/task_log$', views.task_log, name='task_log'),
    url(r'^(?P<uid>\d+)/user_dev$', views.save_user_dev_port, name='save_user_dev_port'),

    url(r'^(?P<uid>\d+)/tel$', views.tels, name='telephones'),
    url(r'^(?P<uid>\d+)/tel/add$', views.tel_add, name='telephone_new'),
    url(r'^(?P<uid>\d+)/tel/del$', views.tel_del, name='telephone_del')
]
