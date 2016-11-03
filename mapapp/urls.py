from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name='maps_home_link'),
    url(r'^get_dots$', views.get_dots, name='maps_get_dots')
]
