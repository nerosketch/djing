from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'mapapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('options/', views.OptionsListView.as_view(), name='options'),
    path('options/add/', views.dot_edit, name='add_dot'),
    path('options/<int:did>/edit/', views.dot_edit, name='edit_dot'),
    path('options/<int:did>/remove/', views.remove, name='remove_dot'),
    path('options/<int:did>/add_dev/', views.add_dev, name='add_dev'),
    path('preload_devices/', views.preload_devices, name='preload_devices'),
    path('get_dots/', views.get_dots, name='get_dots'),

    path('modal_add_dot/', views.modal_add_dot, name='modal_add_dot'),
    path('j_dot_tooltip/', views.dot_tooltip, name='dot_tooltip'),
    path('resolve_dots_by_group/<int:grp_id>/', views.resolve_dots_by_group, name='resolve_dots_by_group'),

    path('to_single_dev/', views.to_single_dev, name='to_single_dev')
]
