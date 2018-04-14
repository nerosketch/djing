from django.conf.urls import url
from . import views

app_name = 'dialing_app'

urlpatterns = [
    url(r'^$', views.LastCallsListView.as_view(), name='home'),
    url(r'^filter$', views.DialsFilterListView.as_view(), name='vfilter'),
    url(r'^to_abon(?P<tel>\+?\d+)$', views.to_abon, name='to_abon'),
    url(r'^requests$', views.VoiceMailRequestsListView.as_view(), name='vmail_request'),
    url(r'^reports$', views.VoiceMailReportsListView.as_view(), name='vmail_report'),
    url(r'^sms/in$', views.InboxSMSListView.as_view(), name='inbox_sms'),
    url(r'^sms/send$', views.send_sms, name='send_sms'),
    url(r'^api/sms$', views.SmsManager.as_view())
]
