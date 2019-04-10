from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from messenger import views


app_name = 'messenger'

urlpatterns = [
    path('', views.MessengerListView.as_view(), name='messengers_list'),
    path('new/', views.AddMessengerCreateView.as_view(), name='add_messenger'),
    path('viber/new/', views.AddMessengerViberCreateView.as_view(), name='add_viber_messenger'),
    path('viber/<slug:slug>/update/', views.UpdateViberMessengerUpdateView.as_view(), name='update_viber_messenger'),
    path('viber/<slug:slug>/delete/', views.RemoveViberMessengerDeleteView.as_view(), name='delete_viber_messenger'),
    path('viber/<slug:slug>/listen/', csrf_exempt(views.ListenViberView.as_view()), name='listen_viber_bot'),
    path('viber/<slug:slug>/set_webhook/', views.SetWebhook.as_view(), name='webhook_viber_bot'),
    path('viber/<slug:slug>/subscribers/', views.SubscribersListView.as_view(), name='subscribers'),
]
