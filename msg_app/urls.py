from django.conf.urls import url
from . import views


app_name = 'msg_app'


urlpatterns = [
    url(r'^$', views.ConversationsListView.as_view(), name='home'),
    url(r'^new$', views.new_conversation, name='new_conversation'),
    url(r'^(?P<conv_id>\d+)/$', views.to_conversation, name='to_conversation'),
    url(r'^(?P<conv_id>\d+)/(?P<msg_id>\d+)/del$', views.remove_msg, name='remove_msg'),
    url(r'^check_news$', views.check_news, name='check_news')
]
