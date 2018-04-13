from django.conf.urls import url, include

from . import views

app_name = 'abonapp'

subscriber_patterns = [
    url(r'^$', views.abonhome, name='abon_home'),
    url(r'^services/$', views.abon_services, name='abon_services'),
    url(r'^amount/$', views.abonamount, name='abon_amount'),
    url(r'^debts/$', views.DebtsListView.as_view(), name='abon_debts'),
    url(r'^pay/$', views.PayHistoryListView.as_view(), name='abon_phistory'),
    url(r'^addinvoice/$', views.add_invoice, name='add_invoice'),
    url(r'^pick/$', views.pick_tariff, name='pick_tariff'),
    url(r'^passport_view/$', views.passport_view, name='passport_view'),
    url(r'^chart/$', views.charts, name='charts'),
    url(r'^dials/$', views.DialsListView.as_view(), name='dials'),
    url(r'^reset_ip/$', views.reset_ip, name='reset_ip'),
    url(r'^extra_field/$', views.make_extra_field, name='extra_field'),
    url(r'^extra_field/(?P<fid>\d+)/delete$', views.extra_field_delete, name='extra_field_delete'),
    url(r'^extra_field/edit$', views.extra_field_change, name='extra_field_edit'),
    url(r'^unsubscribe_service(?P<abon_tariff_id>\d+)/$', views.unsubscribe_service, name='unsubscribe_service'),
    url(r'^dev/$', views.dev, name='dev'),
    url(r'^clear_dev/$', views.clear_dev, name='clear_dev'),
    url(r'^task_log/$', views.TaskLogListView.as_view(), name='task_log'),
    url(r'^user_dev/$', views.save_user_dev_port, name='save_user_dev_port'),
    url(r'^telephones/$', views.tels, name='telephones'),
    url(r'^tel/add/$', views.tel_add, name='telephone_new'),
    url(r'^tel/del/$', views.tel_del, name='telephone_del'),
    url(r'^markers/$', views.EditSibscriberMarkers.as_view(), name='markers_edit'),
    url(r'^periodic_pay$', views.add_edit_periodic_pay, name='add_periodic_pay'),
    url(r'^periodic_pay(?P<periodic_pay_id>\d+)/$', views.add_edit_periodic_pay, name='add_periodic_pay'),
    url(r'^periodic_pay(?P<periodic_pay_id>\d+)/del/$', views.del_periodic_pay, name='del_periodic_pay')
]

group_patterns = [
    url(r'^$', views.PeoplesListView.as_view(), name='people_list'),
    url(r'^addabon$', views.AbonCreateView.as_view(), name='add_abon'),
    url(r'^services$', views.chgroup_tariff, name='ch_group_tariff'),
    url(r'^phonebook$', views.phonebook, name='phonebook'),
    url(r'^export$', views.abon_export, name='abon_export'),
    url(r'^street/add$', views.street_add, name='street_add'),
    url(r'^street/edit', views.street_edit, name='street_edit'),
    url(r'^street/(?P<sid>\d+)/delete$', views.street_del, name='street_del'),
    url(r'^(?P<uname>\w{1,127})/', include(subscriber_patterns))
]

urlpatterns = [

    url(r'^$', views.GroupListView.as_view(), name='group_list'),

    url(r'^fin_report$', views.fin_report, name='fin_report'),

    url(r'^(?P<gid>\d+)/', include(group_patterns)),

    url(r'^log$', views.LogListView.as_view(), name='log'),

    url(r'^del$', views.del_abon, name='del_abon'),

    url(r'^pay$', views.terminal_pay, name='terminal_pay'),

    url(r'^debtors$', views.DebtorsListView.as_view(), name='debtors'),

    url(r'^ping$', views.abon_ping, name='ping'),

    # Api's
    url(r'^api/abons$', views.abons),
    url(r'^api/abon_filter$', views.search_abon),
    url(r'^api/dhcp_lever/$', views.DhcpLever.as_view())
]
