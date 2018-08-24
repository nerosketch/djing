from django.urls import path, re_path
from django.contrib.auth.views import LogoutView

from . import views

app_name = 'account_app'

urlpatterns = [
    path('', views.AccountsListView.as_view(), name='accounts_list'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='acc_app:login'), name='logout'),
    path('login_by_location/', views.location_login, name='llogin'),

    path('me/', views.profile_show, name='profile'),

    path('add/', views.create_profile, name='create_profile'),

    path('settings/', views.ch_info, name='setup_info'),
    path('settings/change_ava/', views.AvatarUpdateView.as_view(), name='setup_avatar'),

    path('<int:uid>/', views.profile_show, name='other_profile'),
    path('<int:uid>/perms/', views.perms, name='setup_perms'),

    re_path('^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)/',
        views.PermissionClassListView.as_view(),
        name='perms_klasses'),

    re_path('^(?P<uid>\d+)/perms/(?P<klass_name>[a-z_]+\.[a-zA-Z_]+)/(?P<obj_id>\d+)/',
        views.perms_edit,
        name='perms_edit'),

    path('<int:uid>/del/', views.delete_profile, name='delete_profile'),

    path('<int:uid>/user_group_access/',
        views.set_abon_groups_permission,
        name='set_abon_groups_permission'),

    path('<int:uid>/manage_responsibility_groups/',
        views.ManageResponsibilityGroups.as_view(),
        name='manage_responsibility_groups')
]
