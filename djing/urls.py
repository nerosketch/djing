from django.urls import path, include
from django.conf import settings

from .views import home

urlpatterns = [
    path('', home),
    path('accounts/', include('accounts_app.urls', namespace='acc_app')),
    path('abons/', include('abonapp.urls', namespace='abonapp')),
    path('tarifs/', include('tariff_app.urls', namespace='tarifs')),
    path('search/', include('searchapp.urls', namespace='searchapp')),
    path('dev/', include('devapp.urls', namespace='devapp')),
    path('map/', include('mapapp.urls', namespace='mapapp')),
    path('statistic/', include('statistics.urls', namespace='statistics')),
    path('tasks/', include('taskapp.urls', namespace='taskapp')),
    path('client/', include('clientsideapp.urls', namespace='client_side')),
    path('msg/', include('msg_app.urls', namespace='msg_app')),
    path('dialing/', include('dialing_app.urls', namespace='dialapp')),
    path('groups/', include('group_app.urls', namespace='group_app')),
    path('ip_pool/', include('ip_pool.urls', namespace='ip_pool')),
    path('gw/', include('gw_app.urls', namespace='gw_app'))

    # Switch language
    #path(r'i18n/', include('django.conf.urls.i18n')),

]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.contrib import admin

    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.extend(staticfiles_urlpatterns())
    urlpatterns.append(path('admin/', admin.site.urls))
