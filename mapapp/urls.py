# -*- coding:utf-8 -*-
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^options$', views.options, name='options'),
    url(r'^options/add$', views.dot, name='add_dot'),
    url(r'^options/(?P<did>\d+)/edit$', views.dot, name='edit_dot'),
    url(r'^options/(?P<did>\d+)/remove$', views.remove, name='remove_dot'),
    url(r'^get_dots$', views.get_dots, name='get_dots'),

    url(r'^modal_add_dot$', views.modal_add_dot, name='modal_add_dot')
]
