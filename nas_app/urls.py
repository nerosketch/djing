from django.conf.urls import url
from nas_app import views


app_name = 'nas_app'


urlpatterns = [
    url(r'^$', view=views.NasListView.as_view(), name='home'),
    url(r'^add$', view=views.NasCreateView.as_view(), name='add'),
    url(r'^(?P<nas_id>\d+)/del$', views.NasDeleteView.as_view(), name='del'),
    url(r'^(?P<nas_id>\d+)/edit$', views.NasUpdateView.as_view(), name='edit'),
]
