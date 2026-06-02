from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.BookingListView.as_view(), name='list'),
    path('calendar/', views.BookingCalendarView.as_view(), name='calendar'),
    path('create/', views.BookingCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.BookingUpdateView.as_view(), name='update'),
    path('<int:pk>/cancel/', views.BookingCancelView.as_view(), name='cancel'),
    path('<int:pk>/check-in/', views.CheckInView.as_view(), name='check_in'),
    path('<int:pk>/check-out/', views.CheckOutView.as_view(), name='check_out'),
    path('<int:pk>/payment/', views.RecordPaymentView.as_view(), name='record_payment'),
    path('<int:pk>/receipt/', views.GenerateReceiptView.as_view(), name='generate_receipt'),
    path('<int:pk>/send-receipt/', views.SendReceiptView.as_view(), name='send_receipt'),
    path('<int:pk>/send-message/', views.SendGuestMessageView.as_view(), name='send_message'),
    path('<int:pk>/note/', views.AddBookingNoteView.as_view(), name='add_note'),
    path('api/calendar-events/', views.CalendarEventsAPIView.as_view(), name='calendar_events'),
]
