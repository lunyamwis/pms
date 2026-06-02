from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    path('', views.IntegrationsDashboardView.as_view(), name='dashboard'),
    path('booking-com/setup/', views.BookingComSetupView.as_view(), name='bookingcom_setup'),
    path('booking-com/webhook/', views.BookingComWebhookView.as_view(), name='bookingcom_webhook'),
    path('airbnb/setup/', views.AirbnbSetupView.as_view(), name='airbnb_setup'),
    path('airbnb/webhook/', views.AirbnbWebhookView.as_view(), name='airbnb_webhook'),
    path('whatsapp/setup/', views.WhatsAppSetupView.as_view(), name='whatsapp_setup'),
    path('whatsapp/webhook/', views.WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('templates/', views.MessageTemplateListView.as_view(), name='templates'),
    path('templates/create/', views.MessageTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.MessageTemplateUpdateView.as_view(), name='template_update'),
    path('sync/', views.SyncReservationsView.as_view(), name='sync'),
    path('logs/', views.IntegrationLogView.as_view(), name='logs'),
]
