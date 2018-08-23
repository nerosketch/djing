from django.urls import path

from . import views

app_name = 'statistics'

urlpatterns = [
    path('', views.home, name='home'),
]
