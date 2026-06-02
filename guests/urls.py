from django.urls import path
from . import views

app_name = 'guests'

urlpatterns = [
    path('', views.GuestListView.as_view(), name='list'),
    path('create/', views.GuestCreateView.as_view(), name='create'),
    path('<int:pk>/', views.GuestDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.GuestUpdateView.as_view(), name='update'),
    path('<int:pk>/blacklist/', views.GuestBlacklistView.as_view(), name='blacklist'),
    path('<int:pk>/document/', views.GuestDocumentUploadView.as_view(), name='upload_document'),
    path('export/', views.GuestExportView.as_view(), name='export'),
]
