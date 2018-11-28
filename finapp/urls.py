from django.urls import path
from finapp import views


app_name = 'finapp'

urlpatterns = [
    path('', views.AllTimeGatewaysListView.as_view(),
         name='alltime_gateways_list'),

    # path('fin_report/', views.BasicFinReport.as_view(), name='fin_report'),
    # path('pay/', views.terminal_pay, name='terminal_pay'),

    path('add/', views.AddAllTimeGateway.as_view(),
         name='add_alltime_gateway'),

    path('<slug:pay_slug>/pay_history/', views.PayHistoryListView.as_view(),
         name='pay_history'),

    path('<slug:pay_slug>/make_pay/', views.AllTimePay.as_view(),
         name='all_time_pay'),

    path('<slug:pay_slug>/edit/', views.EditPayUpdateView.as_view(),
         name='edit_pay_gw'),
]
