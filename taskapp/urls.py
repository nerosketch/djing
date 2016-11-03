from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name='task_home'),
    url(r'^(?P<task_id>\d+)/edit$', views.task_add_edit, name='task_edit'),
    url(r'^(?P<task_id>\d+)/delete$', views.task_delete, name='task_delete'),
    url(r'^(?P<task_id>\d+)/fin$', views.task_finish, name='task_finish'),
    url(r'^(?P<task_id>\d+)/begin$', views.task_begin, name='task_begin'),
    url(r'^add$', views.task_add_edit, name='task_add'),
    url(r'^active$', views.active_tasks, name='active_tasks'),
    url(r'^finished$', views.finished_tasks, name='finished_tasks'),
    url(r'^own$', views.own_tasks, name='own_tasks'),
    url(r'^all$', views.all_tasks, name='all_tasks')
]
