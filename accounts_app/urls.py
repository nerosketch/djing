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
    url(r'^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)$', views.perms_klasses, name='perms_klasses'),
    url(r'^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)/(?P<obj_id>\d+)$', views.perms_edit, name='perms_edit'),
    url(r'^(?P<uid>\d+)/chgroup$', views.chgroup, name='profile_setup_group'),
    url(r'^(?P<uid>\d+)/del$', views.delete_profile, name='delete_profile'),

    url(r'^(?P<uid>\d+)/user_group_access$', views.set_abon_groups_permission, name='set_abon_groups_permission')

]