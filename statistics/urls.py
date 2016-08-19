from django.conf.urls import url, include
import views

urlpatterns = [
    url(r'^$', views.home, name='stat_home'),
]
