from django.urls import path
from docsapp import views

app_name = 'docsapp'


urlpatterns = [
    path('', views.DocumentsListView.as_view(), name='docs_list'),
    path('add/', views.DocumentCreateView.as_view(), name='doc_add'),
    path('<int:pk>/', views.DocumentUpdateView.as_view(), name='doc_edit'),
    path('<int:pk>/del/', views.DocumentDeleteView.as_view(), name='doc_del'),
    path('<int:pk>/<slug:uname>/render/', views.RenderDocument.as_view(), name='doc_render'),
    path('<slug:account_name>/simple_list/', views.SimpleListView.as_view(), name='simple_list'),
]
