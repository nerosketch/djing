from django.conf.urls import url

from . import views

app_name = 'account_app'

urlpatterns = [

    url(r'^login/', views.to_signin, name='login'),
    url(r'^logout/', views.SignOut.as_view(), name='logout'),

    url(r'^me$', views.profile_show, name='profile'),

    url(r'^$', views.AccountsListView.as_view(), name='accounts_list'),

    url(r'^add$', views.create_profile, name='create_profile'),

    url(r'^settings$', views.ch_info, name='setup_info'),
    url(r'^settings/change_ava$', views.ch_ava, name='setup_avatar'),

    url(r'^(?P<uid>\d+)$', views.profile_show, name='other_profile'),
    url(r'^(?P<uid>\d+)/perms$', views.perms, name='setup_perms'),

    url(r'^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)$',
        views.PermissionClassListView.as_view(),
        name='perms_klasses'),

    url(r'^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)/(?P<obj_id>\d+)$',
        views.perms_edit,
        name='perms_edit'),

    url(r'^(?P<uid>\d+)/del$', views.delete_profile, name='delete_profile'),

    url(r'^(?P<uid>\d+)/user_group_access$',
        views.set_abon_groups_permission,
        name='set_abon_groups_permission'),

    url(r'^(?P<uid>\d+)/manage_responsibility_groups/$',
        views.ManageResponsibilityGroups.as_view(),
        name='manage_responsibility_groups')
]
