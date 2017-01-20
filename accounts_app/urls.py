# -*- coding:utf-8 -*-
from django.conf.urls import url

from . import views


urlpatterns = [

    url(r'^login/', views.to_signin, name='login'),
    url(r'^logout/', views.sign_out, name='logout'),

    url(r'^me$', views.profile_show, name='profile'),

    url(r'^$', views.acc_list, name='accounts_list'),

    url(r'^add$', views.create_profile, name='create_profile'),

    url(r'^settings$', views.ch_info, name='setup_info'),
    url(r'^settings/change_ava$', views.ch_ava, name='setup_avatar'),

    url(r'^(?P<uid>\d+)$', views.profile_show, name='other_profile'),
    url(r'^(?P<uid>\d+)/perms$', views.perms, name='setup_perms'),
    url(r'^(?P<uid>\d+)/chgroup$', views.chgroup, name='profile_setup_group'),
    url(r'^(?P<uid>\d+)/del$', views.delete_profile, name='delete_profile'),

    # назначить задание
    url(r'^(?P<uid>\d+)/appoint_task$', views.appoint_task, name='appoint_task'),

    url(r'^group/$', views.groups, name='groups_list'),
    url(r'^group/(?P<uid>\d+)$', views.group, name='group_link')

]