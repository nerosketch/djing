from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name='privmsg_home'),
    url(r'^delitem_(?P<id>\d+)$', views.delitem, name='privmsg_delitem'),
    url(r'^write', views.send_message, name='privmsg_send_message')
]
