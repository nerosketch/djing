from django.conf.urls import url
from . import views

app_name = 'group_app'

urlpatterns = [
    url(r'^$', views.GroupListView.as_view(), name='group_list'),
    url(r'^add/$', views.AddGroupView.as_view(), name='add'),
    url(r'^(?P<group_id>\d{1,6})/edit/$', views.EditGroupView.as_view(), name='edit')
]
