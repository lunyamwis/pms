from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    # Agent listings
    path('', views.AgentListView.as_view(), name='list'),
    path('<int:pk>/', views.AgentDetailView.as_view(), name='detail'),
    
    # Agent dashboard
    path('dashboard/', views.AgentDashboardView.as_view(), name='dashboard'),
    path('dashboard/properties/', views.AgentPropertiesView.as_view(), name='properties'),
    path('dashboard/inquiries/', views.AgentInquiriesView.as_view(), name='inquiries'),
    path('dashboard/reviews/', views.AgentReviewsView.as_view(), name='reviews'),
    path('dashboard/messages/', views.AgentMessagesView.as_view(), name='messages'),
    path('dashboard/analytics/', views.AgentAnalyticsView.as_view(), name='analytics'),
    
    # Agent profile management
    path('profile/edit/', views.AgentProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/settings/', views.AgentSettingsView.as_view(), name='settings'),
] 