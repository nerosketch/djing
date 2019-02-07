from django.urls import path
from . import views

app_name = 'msg_app'

urlpatterns = [
    path('', views.ConversationsListView.as_view(), name='home'),
    path('new/', views.new_conversation, name='new_conversation'),
    path('<int:conv_id>/', views.to_conversation, name='to_conversation'),
    path('<int:conv_id>/<int:msg_id>/del/', views.remove_msg, name='remove_msg')
]
