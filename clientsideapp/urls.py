from django.urls import path
from . import views

app_name = 'clientsideapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('pays/', views.pays, name='pays'),
    path('services/', views.services, name='services'),
    path('services/<int:srv_id>/buy/', views.buy_service, name='buy_service'),
    path('debts/', views.debts_list, name='debts'),
    path('debts/<int:d_id>/', views.debt_buy, name='debt_buy'),
    path('tasks/', views.task_history, name='task_history')
]
