# -*- coding:utf-8 -*-
from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name='client_home'),
    url(r'^pays$', views.pays, name='client_pays'),
    url(r'^buy$', views.buy_service, name='client_buy'),
    url(r'^debts$', views.debts_list, name='client_debts'),
    url(r'^debts/(?P<d_id>\d+)$', views.debt_buy, name='client_debt_buy')
]
