from django.conf.urls import url, include
from django.contrib import admin
import settings
from views import home

urlpatterns = [
    url(r'^$', home),
    url(r'^accounts/', include('accounts_app.urls')),
    url(r'^im/', include('privatemessage.urls')),
    url(r'^abons/', include('abonapp.urls')),
    url(r'^tarifs/', include('tariff_app.urls')),
    url(r'^ip_pool/', include('ip_pool.urls')),
    url(r'^search/', include('searchapp.urls')),
    url(r'^dev/', include('devapp.urls')),
    url(r'^map/', include('mapapp.urls')),
    url(r'^statistic/', include('statistics.urls')),
    url(r'^tasks/', include('taskapp.urls')),
    url(r'^admin/', admin.site.urls),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
