from django.conf.urls import url, include
from django.contrib import admin

import settings
from views import home


urlpatterns = [
    url(r'^$', home),
    url(r'^accounts/', include('accounts_app.urls', namespace='acc_app')),
    url(r'^im/', include('privatemessage.urls', namespace='privmsg')),
    url(r'^abons/', include('abonapp.urls', namespace='abonapp')),
    url(r'^tarifs/', include('tariff_app.urls', namespace='tarifs')),
    url(r'^ip_pool/', include('ip_pool.urls', namespace='ip_pool')),
    url(r'^search/', include('searchapp.urls', namespace='searchapp')),
    url(r'^dev/', include('devapp.urls', namespace='devapp')),
    url(r'^gmap/', include('gmap.urls')),
    url(r'^statistic/', include('statistics.urls', namespace='statistics')),
    url(r'^tasks/', include('taskapp.urls', namespace='taskapp')),
    url(r'^client/', include('clientsideapp.urls', namespace='client_side')),
    url(r'^admin/', admin.site.urls)
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
