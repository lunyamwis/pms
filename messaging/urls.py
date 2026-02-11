from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Messaging
    path('', views.InboxView.as_view(), name='inbox'),
    path('sent/', views.SentMessagesView.as_view(), name='sent'),
    path('archived/', views.ArchivedMessagesView.as_view(), name='archived'),
    path('compose/', views.ComposeMessageView.as_view(), name='compose'),
    path('conversation/<int:pk>/', views.ConversationView.as_view(), name='conversation'),
    
    # Message actions
    path('message/<int:pk>/delete/', views.DeleteMessageView.as_view(), name='delete_message'),
    path('message/<int:pk>/archive/', views.ArchiveMessageView.as_view(), name='archive_message'),
    path('message/<int:pk>/mark-read/', views.MarkMessageReadView.as_view(), name='mark_read'),
    path('message/<int:pk>/mark-unread/', views.MarkMessageUnreadView.as_view(), name='mark_unread'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    path('notifications/<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
] 