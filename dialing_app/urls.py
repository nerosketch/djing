from django.urls import path, re_path
from . import views

app_name = 'dialing_app'

urlpatterns = [
    path('', views.LastCallsListView.as_view(), name='home'),
    path('filter/', views.DialsFilterListView.as_view(), name='vfilter'),
    re_path('^to_abon(?P<tel>\+?\d+)/$', views.to_abon, name='to_abon'),
    path('requests/', views.VoiceMailRequestsListView.as_view(), name='vmail_request'),
    path('reports/', views.VoiceMailReportsListView.as_view(), name='vmail_report'),
    path('sms/in/', views.InboxSMSListView.as_view(), name='inbox_sms'),
    path('sms/send/', views.send_sms, name='send_sms'),
    path('api/sms/', views.SmsManager.as_view())
]
