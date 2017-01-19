from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.devices, name='devs'),
    url(r'^add$', views.dev, name='add'),
    url(r'^(?P<did>\d+)$', views.devview, name='view'),
    url(r'^(?P<did>\d+)/del$', views.devdel, name='del'),
    url(r'^(?P<devid>\d+)/edit$', views.dev, name='edit'),
    url(r'^(?P<did>\d+)/(?P<portid>\d+)_(?P<status>[0-1]{1})$', views.toggle_port, name='port_toggle')
]
