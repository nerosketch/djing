from django.conf.urls import url
from ip_pool import views

app_name = 'ip_pool'

urlpatterns = [
    url('^$', views.NetworksListView.as_view(), name='networks'),
    url('^network_add/$', views.NetworkCreateView.as_view(), name='net_add'),
    url('^(?P<net_id>\d{1,6})/$', views.IpEmployedListView.as_view(), name='ip_list'),
    url('^(?P<net_id>\d{1,6})/edit$', views.NetworkUpdateView.as_view(), name='net_edit'),
]
