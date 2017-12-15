from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.group_list, name='group_list'),
    url(r'^devices_without_groups$', views.devices_null_group, name='devices_null_group'),
    url(r'^fix_onu/$', views.fix_onu, name='fix_onu'),
    url(r'^(?P<grp>\d+)$', views.devices, name='devs'),
    url(r'^(?P<grp>\d+)/add$', views.dev, name='add'),
    url(r'^(\d+)/(?P<did>\d+)$', views.devview, name='view'),
    url(r'^(\d+)/(?P<did>\d+)/del$', views.devdel, name='del'),
    url(r'^(?P<grp>\d+)/(?P<did>\d+)/add$', views.add_single_port, name='add_port'),
    url(r'^(?P<grp>\d+)/(?P<devid>\d+)/edit$', views.dev, name='edit'),
    url(r'^(\d+)/(?P<devid>\d+)/ports$', views.manage_ports, name='manage_ports'),
    url(r'^(\d+)/(?P<devid>\d+)/ports_add', views.add_ports, name='add_ports'),
    url(r'^(\d+)/(?P<did>\d+)/(?P<portid>\d+)_(?P<status>[0-1]{1})$', views.toggle_port, name='port_toggle'),
    url(r'^(?P<grp>\d+)/(?P<did>\d+)/(?P<portid>\d+)/del$', views.delete_single_port, name='del_port'),
    url(r'^(?P<grp>\d+)/(?P<did>\d+)/(?P<pid>\d+)/edit$', views.edit_single_port, name='edit_port'),
    url(r'^fix_device_group/(?P<did>\d+)$', views.fix_device_group, name='fix_device_group'),
    url(r'^search_dev$', views.search_dev)
]
