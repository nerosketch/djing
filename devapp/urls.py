from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.devices, name='devs_link'),
    url(r'^add$', views.dev, name='devs_add_link'),
    url(r'^(?P<did>\d+)$', views.devview, name='devs_view_link'),
    url(r'^(?P<did>\d+)/del$', views.devdel, name='devs_del_link'),
    url(r'^(?P<devid>\d+)/edit$', views.dev, name='devs_edit_link'),
]
