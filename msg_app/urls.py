from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^new$', views.new_conversation, name='new_conversation'),
    url(r'^(?P<conv_id>\d+)/$', views.to_conversation, name='to_conversation'),
    url(r'^(?P<conv_id>\d+)/(?P<msg_id>\d+)/del$', views.remove_msg, name='remove_msg')
]
