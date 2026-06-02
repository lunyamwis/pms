from django.urls import path
from . import views

app_name = 'housekeeping'

urlpatterns = [
    path('', views.HousekeepingDashboardView.as_view(), name='dashboard'),
    path('tasks/', views.CleaningTaskListView.as_view(), name='task_list'),
    path('tasks/create/', views.CleaningTaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.CleaningTaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/update-status/', views.UpdateTaskStatusView.as_view(), name='task_update_status'),
    path('maintenance/', views.MaintenanceRequestListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', views.MaintenanceRequestCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/', views.MaintenanceRequestDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/<int:pk>/update/', views.MaintenanceRequestUpdateView.as_view(), name='maintenance_update'),
    path('room-service/', views.RoomServiceListView.as_view(), name='room_service_list'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/create/', views.StaffCreateView.as_view(), name='staff_create'),
]
