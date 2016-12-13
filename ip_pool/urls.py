# -*- coding:utf-8 -*-
from django.conf.urls import url

import views


urlpatterns = [

    url(r'^$', views.home, name='home'),
    url(r'^range$', views.ips, name='ips'),
    url(r'^del$', views.del_pool, name='ips_del'),
    url(r'^add$', views.add_pool, name='add'),

    url(r'^delip$', views.delip, name='del_ip')
]
