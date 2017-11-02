from django.conf.urls import url, include

from . import settings
from .views import home


urlpatterns = [
    url(r'^$', home),
    url(r'^accounts/', include('accounts_app.urls', namespace='acc_app')),
    url(r'^abons/', include('abonapp.urls', namespace='abonapp')),
    url(r'^tarifs/', include('tariff_app.urls', namespace='tarifs')),
    url(r'^search/', include('searchapp.urls', namespace='searchapp')),
    url(r'^dev/', include('devapp.urls', namespace='devapp')),
    url(r'^map/', include('mapapp.urls', namespace='mapapp')),
    url(r'^statistic/', include('statistics.urls', namespace='statistics')),
    url(r'^tasks/', include('taskapp.urls', namespace='taskapp')),
    url(r'^client/', include('clientsideapp.urls', namespace='client_side')),
    url(r'^msg/', include('msg_app.urls', namespace='msg_app')),
    url(r'^dialing/', include('dialing_app.urls', namespace='dialapp'))
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.contrib import admin

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [url(r'^admin/', admin.site.urls)]
