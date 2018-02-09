# -*- coding:utf-8 -*-
from django.conf.urls import url

from . import views


app_name = 'mapapp'


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^options$', views.OptionsListView.as_view(), name='options'),
    url(r'^options/add$', views.dot, name='add_dot'),
    url(r'^options/(?P<did>\d+)/edit$', views.dot, name='edit_dot'),
    url(r'^options/(?P<did>\d+)/remove$', views.remove, name='remove_dot'),
    url(r'^options/(?P<did>\d+)/add_dev$', views.add_dev, name='add_dev'),
    url(r'^preload_devices$', views.preload_devices, name='preload_devices'),
    url(r'^get_dots$', views.get_dots, name='get_dots'),

    url(r'^modal_add_dot$', views.modal_add_dot, name='modal_add_dot'),
    url(r'^j_dot_tooltip$', views.dot_tooltip, name='dot_tooltip'),
    url(r'^resolve_dots_by_group(?P<grp_id>\d+)$', views.resolve_dots_by_group, name='resolve_dots_by_group')

]
