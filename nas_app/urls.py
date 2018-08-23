from django.urls import path
from nas_app import views


app_name = 'nas_app'


urlpatterns = [
    path('', view=views.NasListView.as_view(), name='home'),
    path('add/', view=views.NasCreateView.as_view(), name='add'),
    path('<int:nas_id>/del/', views.NasDeleteView.as_view(), name='del'),
    path('<int:nas_id>/edit/', views.NasUpdateView.as_view(), name='edit'),
]
