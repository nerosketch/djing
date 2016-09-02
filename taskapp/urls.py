from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.home, name='task_home'),
    url(r'^(?P<task_id>\d+)/edit$', views.task_add_edit, name='task_edit'),
    url(r'^(?P<task_id>\d+)/delete$', views.task_delete, name='task_delete'),
    url(r'^add$', views.task_add_edit, name='task_add')
]
