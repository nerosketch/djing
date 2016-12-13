from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^delitem_(?P<id>\d+)$', views.delitem, name='delitem'),
    url(r'^write', views.send_message, name='send_message')
]
