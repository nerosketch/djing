from django.conf.urls import url
from . import views

app_name = 'devapp'

urlpatterns = [
    url(r'^$', views.GroupsListView.as_view(), name='group_list'),
    url(r'^devices_without_groups$', views.DevicesWithoutGroupsListView.as_view(), name='devices_null_group'),
    url(r'^fix_onu/$', views.fix_onu, name='fix_onu'),
    url(r'^(?P<group_id>\d+)$', views.DevicesListView.as_view(), name='devs'),
    url(r'^(?P<group_id>\d+)/add$', views.dev, name='add'),
    url(r'^(\d+)/(?P<device_id>\d+)$', views.devview, name='view'),
    url(r'^(\d+)/(?P<device_id>\d+)/del$', views.DeviceVeleteView.as_view(), name='del'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/add$', views.add_single_port, name='add_port'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/edit$', views.dev, name='edit'),
    url(r'^(\d+)/(?P<device_id>\d+)/ports$', views.manage_ports, name='manage_ports'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/ports/(?P<port_id>\d+)/fix_port_conflict$', views.fix_port_conflict,
        name='fix_port_conflict'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/ports/(?P<port_id>\d+)/show_subscriber_on_port$',
        views.ShowSubscriberOnPort.as_view(), name='show_subscriber_on_port'),
    url(r'^(\d+)/(?P<device_id>\d+)/ports_add', views.add_ports, name='add_ports'),
    url(r'^(\d+)/(?P<device_id>\d+)/(?P<portid>\d+)_(?P<status>[0-1]{1})$', views.toggle_port, name='port_toggle'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/(?P<portid>\d+)/del$', views.delete_single_port, name='del_port'),
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/(?P<port_id>\d+)/edit$', views.edit_single_port, name='edit_port'),
    url(r'^fix_device_group/(?P<device_id>\d+)$', views.fix_device_group, name='fix_device_group'),
    url(r'^search_dev$', views.search_dev),

    # ZTE ports under fibers
    url(r'^(?P<group_id>\d+)/(?P<device_id>\d+)/(?P<fiber_id>\d+)$', views.zte_port_view, name='zte_port_view'),

    # Monitoring api
    url(r'^on_device_event/$', views.OnDeviceMonitoringEvent.as_view()),

    # Nagios mon generate
    url(r'^nagios/hosts/$', views.NagiosObjectsConfView.as_view(), name='nagios_objects_conf'),
    url(r'^api/getall/$', views.DevicesGetListView.as_view())
]
