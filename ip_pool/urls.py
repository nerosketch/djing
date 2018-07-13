from django.conf.urls import url
from ip_pool import views
from ip_pool import models

app_name = 'ip_pool'

urlpatterns = [
    url('^$', views.NetworksListView.as_view(), name='networks'),
    url('^network_add/$', views.NetworkCreateView.as_view(), name='net_add'),
    url('^(?P<net_id>\d{1,6})/$', views.IpLeasesListView.as_view(), name='ip_leases_list'),
    url('^(?P<net_id>\d{1,6})/edit/$', views.NetworkUpdateView.as_view(), name='net_edit'),
    url('^(?P<net_id>\d{1,6})/del/$', views.NetworkDeleteView.as_view(), name='net_delete'),
    url('^(?P<net_id>\d{1,6})/group_attach/$', views.network_in_groups, name='net_groups')
]

for dev_kind_code, _ in models.NetworkModel.NETWORK_KINDS:
    urlpatterns.append(url(
        '^networks_%s/$' % dev_kind_code,
        views.NetworksListView.as_view(device_kind_code=dev_kind_code),
        name='networks_%s' % dev_kind_code
    ))
