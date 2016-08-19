# -*- coding:utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [

    url(r'^$', views.home, name='pool_home_link'),
    url(r'^range$', views.ips, name='pool_ips_link'),
    url(r'^del$', views.del_pool, name='pool_ips_del_link'),
    url(r'^add$', views.add_pool, name='pool_add_link'),

    url(r'^delip$', views.delip, name='pool_del_ip_link')
]