# -*- coding:utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^pays$', views.pays, name='pays'),
    url(r'^services$', views.services, name='services'),
    url(r'^services/(?P<srv_id>\d+)/buy$', views.buy_service, name='buy_service'),
    url(r'^services/(?P<srv_id>\d+)/finish$', views.complete_service, name='complete_service'),
    url(r'^services/(?P<srv_id>\d+)/unsubscribe$', views.unsubscribe_service, name='unsubscribe_service'),
    url(r'^services/(?P<srv_id>\d+)/activate$', views.activate_service, name='activate_service'),
    url(r'^debts$', views.debts_list, name='debts'),
    url(r'^debts/(?P<d_id>\d+)$', views.debt_buy, name='debt_buy')
]
