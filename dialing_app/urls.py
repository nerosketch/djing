from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^to_abon(?P<tel>\+?\d+)$', views.to_abon, name='to_abon'),
    url(r'^voicemail$', views.vmail, name='vmail')
]
