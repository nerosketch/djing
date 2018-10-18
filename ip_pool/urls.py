from django.urls import path
from ip_pool import views
from ip_pool import models

app_name = 'ip_pool'

urlpatterns = [
    path('', views.NetworksListView.as_view(), name='networks'),
    path('network_add/', views.NetworkCreateView.as_view(), name='net_add'),
    path('<int:net_id>/edit/', views.NetworkUpdateView.as_view(), name='net_edit'),
    path('<int:net_id>/del/', views.NetworkDeleteView.as_view(), name='net_delete'),
    path('<int:net_id>/group_attach/', views.network_in_groups, name='net_groups')
]

for dev_kind_code, _ in models.NetworkModel.NETWORK_KINDS:
    _url_name = 'networks_%s/' % dev_kind_code
    urlpatterns.append(path(
        _url_name,
        views.NetworksListView.as_view(device_kind_code=dev_kind_code),
        name=_url_name
    ))
