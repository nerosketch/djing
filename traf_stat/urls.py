from django.urls import path

from traf_stat.views import home

app_name = 'traf_stat'

urlpatterns = [
    path('', home, name='home'),
]
