from django.urls import path, include, re_path

from . import views

app_name = 'abonapp'

subscriber_patterns = [
    path('', views.AbonHomeUpdateView.as_view(), name='abon_home'),
    path('services/', views.abon_services, name='abon_services'),
    path('amount/', views.abonamount, name='abon_amount'),
    path('debts/', views.DebtsListView.as_view(), name='abon_debts'),
    path('pay/', views.PayHistoryListView.as_view(), name='abon_phistory'),
    path('addinvoice/', views.add_invoice, name='add_invoice'),
    path('pick/', views.pick_tariff, name='pick_tariff'),
    path('passport_view/', views.PassportUpdateView.as_view(), name='passport_view'),
    path('chart/', views.charts, name='charts'),
    path('dials/', views.DialsListView.as_view(), name='dials'),
    # path('reset_ip/', views.reset_ip, name='reset_ip'),
    path('unsubscribe_service/<int:abon_tariff_id>/', views.unsubscribe_service, name='unsubscribe_service'),
    path('dev/', views.dev, name='dev'),
    path('del/', views.DelAbonDeleteView.as_view(), name='del_abon'),
    path('clear_dev/', views.clear_dev, name='clear_dev'),
    path('task_log/', views.TaskLogListView.as_view(), name='task_log'),
    path('user_dev/', views.save_user_dev_port, name='save_user_dev_port'),
    path('telephones/', views.tels, name='telephones'),
    path('tel/add/', views.tel_add, name='telephone_new'),
    path('tel/del/', views.tel_del, name='telephone_del'),
    path('markers/', views.EditSibscriberMarkers.as_view(), name='markers_edit'),
    path('session/<int:lease_id>/free/', views.user_session_toggle, {'action': 'free'}, name='user_session_free'),
    path('session/<int:lease_id>/start/', views.user_session_toggle, {'action': 'start'}, name='user_session_start'),
    path('periodic_pay/', views.add_edit_periodic_pay, name='add_periodic_pay'),
    path('periodic_pay/<int:periodic_pay_id>/', views.add_edit_periodic_pay, name='add_periodic_pay'),
    path('periodic_pay/<int:periodic_pay_id>/del/', views.del_periodic_pay, name='del_periodic_pay'),
    path('lease/add/', views.lease_add, name='lease_add'),
    path('ping/', views.abon_ping, name='ping'),
    path('set_auto_continue_service/', views.set_auto_continue_service, name='set_auto_continue_service')
]

group_patterns = [
    path('', views.PeoplesListView.as_view(), name='people_list'),
    path('addabon/', views.AbonCreateView.as_view(), name='add_abon'),
    path('services/', views.chgroup_tariff, name='ch_group_tariff'),
    path('phonebook/', views.phonebook, name='phonebook'),
    path('export/', views.abon_export, name='abon_export'),
    path('street/add/', views.street_add, name='street_add'),
    path('street/edit', views.street_edit, name='street_edit'),
    path('street/<int:sid>/delete/', views.street_del, name='street_del'),
    path('active_networks/', views.active_nets, name='active_nets'),
    path('attach_nas/', views.attach_nas, name='attach_nas'),
    re_path('^(?P<uname>\w{1,127})/', include(subscriber_patterns))
]

urlpatterns = [
    path('', views.GroupListView.as_view(), name='group_list'),
    path('fin_report/', views.fin_report, name='fin_report'),
    path('<int:gid>/', include(group_patterns)),
    path('log/', views.LogListView.as_view(), name='log'),
    path('pay/', views.terminal_pay, name='terminal_pay'),
    path('debtors/', views.DebtorsListView.as_view(), name='debtors'),
    path('contacts/vcards/', views.vcards, name='vcards'),

    # Api's
    path('api/abons/', views.abons),
    path('api/abon_filter/', views.search_abon),
    path('api/dhcp_lever/', views.DhcpLever.as_view())
]
