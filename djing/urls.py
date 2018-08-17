from django.conf.urls import url, include
from django.conf import settings

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
    url(r'^dialing/', include('dialing_app.urls', namespace='dialapp')),
    url(r'^groups/', include('group_app.urls', namespace='group_app')),
    url(r'^ip_pool/', include('ip_pool.urls', namespace='ip_pool')),
    url(r'^nas/', include('nas_app.urls', namespace='nas_app'))

    # Switch language
    #url(r'^i18n/', include('django.conf.urls.i18n')),

]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.contrib import admin

    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.extend(staticfiles_urlpatterns())
    urlpatterns.append(url(r'^admin/', admin.site.urls))
