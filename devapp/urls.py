from django.urls import path, re_path
from . import views

app_name = 'devapp'

urlpatterns = [
    path('', views.GroupsListView.as_view(), name='group_list'),
    path('devices_without_groups/',
         views.DevicesWithoutGroupsListView.as_view(),
         name='devices_null_group'),
    path('fix_onu/', views.fix_onu, name='fix_onu'),
    path('<int:group_id>/', views.DevicesListView.as_view(), name='devs'),
    path('<int:group_id>/add/', views.DeviceCreateView.as_view(), name='add'),
    path('<int:group_id>/<int:device_id>/', views.devview, name='view'),
    path('<int:group_id>/<int:device_id>/del/',
         views.DeviceDeleteView.as_view(), name='del'),
    path('<int:group_id>/<int:device_id>/add/', views.add_single_port,
         name='add_port'),
    path('<int:group_id>/<int:device_id>/edit/', views.DeviceUpdate.as_view(),
         name='edit'),
    path('<int:group_id>/<int:device_id>/edit_extra/',
         views.DeviceUpdateExtra.as_view(), name='extra_data_edit'),
    path(
        '<int:group_id>/<int:device_id>/ports/<int:port_id>/fix_port_conflict/',
        views.fix_port_conflict,
        name='fix_port_conflict'),
    path(
        '<int:group_id>/<int:device_id>/ports/<int:port_id>/show_subscriber_on_port/',
        views.ShowSubscriberOnPort.as_view(), name='show_subscriber_on_port'),
    path('<int:group_id>/<int:device_id>/ports_add/', views.add_ports,
         name='add_ports'),
    path('<int:group_id>/<int:device_id>/register_device/',
         views.register_device, name='dev_register'),
    re_path('^(\d+)/(?P<device_id>\d+)/(?P<port_id>\d+)_(?P<status>[0-1]{1})$',
            views.toggle_port, name='port_toggle'),
    path('<int:group_id>/<int:device_id>/<int:port_id>/del/',
         views.delete_single_port, name='del_port'),
    path('<int:group_id>/<int:device_id>/<int:port_id>/edit/',
         views.edit_single_port, name='edit_port'),
    path('fix_device_group/<int:device_id>/', views.fix_device_group,
         name='fix_device_group'),
    path('search_dev/', views.search_dev),

    # ZTE ports under fibers
    path('<int:group_id>/<int:device_id>/<int:fiber_id>/',
         views.zte_port_view_uncfg, name='zte_port_view_uncfg'),

    # Monitoring api
    path('on_device_event/', views.OnDeviceMonitoringEvent.as_view()),

    # Nagios mon generate
    path('nagios/hosts/', views.nagios_objects_conf,
         name='nagios_objects_conf'),
    path('api/getall/', views.DevicesGetListView.as_view(),
         name='nagios_get_all_hosts')
]
