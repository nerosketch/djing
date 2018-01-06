from django.conf.urls import url
from . import views


app_name = 'dialing_app'


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^filter$', views.vfilter, name='vfilter'),
    url(r'^to_abon(?P<tel>\+?\d+)$', views.to_abon, name='to_abon'),
    url(r'^requests$', views.vmail_request, name='vmail_request'),
    url(r'^reports$', views.vmail_report, name='vmail_report'),
    url(r'^sms/in$', views.inbox_sms, name='inbox_sms'),
    url(r'^sms/send$', views.send_sms, name='send_sms')
]
