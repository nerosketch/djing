from django.urls import path
from new_customers import views


app_name = 'new_customers'


urlpatterns = [
    path('', views.CustomersList.as_view(), name='customers_list'),
    path('new/', views.CustomerNew.as_view(), name='new_user'),
    path('<int:uid>/', views.CustomerDetail.as_view(), name='user'),
]
