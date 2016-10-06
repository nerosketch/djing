# -*- coding:utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [

    url(r'^login/', views.to_signin, name='login_link'),
    url(r'^logout/', views.sign_out, name='logout_link'),

    url(r'^me$', views.profile_show, name='profile'),

    url(r'^$', views.acc_list, name='accounts_list'),

    url(r'^add$', views.create_profile, name='create_profile_link'),

    url(r'^settings$', views.ch_info, name='settings_chinfo_link'),
    url(r'^settings/change_ava$', views.ch_ava, name='settings_chava_link'),

    url(r'^(?P<id>\d+)$', views.profile_show, name='other_profile'),
    url(r'^(?P<id>\d+)/perms$', views.perms, name='profile_perms_link'),
    url(r'^(?P<uid>\d+)/chgroup$', views.chgroup, name='profile_chgroup_link'),
    url(r'^(?P<uid>\d+)/del$', views.delete_profile, name='delete_profile_link'),

    # назначить задание
    url(r'^(?P<uid>\d+)/appoint_task$', views.appoint_task, name='profile_appoint_task'),

    url(r'^group/$', views.groups, name='profile_groups_list'),
    url(r'^group/(?P<id>\d+)$', views.group, name='profile_group_link')

]