from django.conf.urls import url

from . import views


app_name = 'taskapp'


urlpatterns = [
    url(r'^$', views.NewTasksView.as_view(), name='home'),
    url(r'^(?P<task_id>\d+)$', views.TaskUpdateView.as_view(), name='edit'),
    url(r'^(?P<task_id>\d+)/delete$', views.task_delete, name='delete'),
    url(r'^(?P<task_id>\d+)/fin$', views.task_finish, name='finish'),
    url(r'^(?P<task_id>\d+)/fail$', views.task_failed, name='fail'),
    url(r'^(?P<task_id>\d+)/remind', views.remind, name='remind'),
    url(r'^(?P<task_id>\d+)/comment/add$', views.NewCommentView.as_view(), name='comment_add'),
    url(r'^(?P<task_id>\d+)/comment/(?P<comment_id>\d{1,8})/remove$', views.DeleteCommentView.as_view(), name='comment_del'),
    url(r'^add$', views.TaskUpdateView.as_view(), name='add'),
    url(r'^failed$', views.FailedTasksView.as_view(), name='failed_tasks'),
    url(r'^finished$', views.FinishedTaskListView.as_view(), name='finished_tasks'),
    url(r'^own$', views.OwnTaskListView.as_view(), name='own_tasks'),
    url(r'^my$', views.MyTaskListView.as_view(), name='my_tasks'),
    url(r'^all$', views.AllTasksListView.as_view(), name='all_tasks'),
    url(r'^empty$', views.EmptyTasksListView.as_view(), name='empty_tasks'),
    url(r'^check_news$', views.check_news, name='check_news')
]
