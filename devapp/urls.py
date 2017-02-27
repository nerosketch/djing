from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.group_list, name='group_list'),
    url(r'^add$', views.dev, name='add'),
    url(r'^devices_without_groups$', views.devices_null_group, name='devices_null_group'),
    url(r'^(?P<grp>\d+)$', views.devices, name='devs'),
    url(r'^(\d+)/(?P<did>\d+)$', views.devview, name='view'),
    url(r'^(\d+)/(?P<did>\d+)/del$', views.devdel, name='del'),
    url(r'^(\d+)/(?P<devid>\d+)/edit$', views.dev, name='edit'),
    url(r'^(\d+)/(?P<did>\d+)/(?P<portid>\d+)_(?P<status>[0-1]{1})$', views.toggle_port, name='port_toggle')
]
