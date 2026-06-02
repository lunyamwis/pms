from django.contrib import admin
from .models import CleaningTask, MaintenanceRequest, RoomServiceOrder, HousekeepingStaff


@admin.register(HousekeepingStaff)
class HousekeepingStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ['asset_property' , 'task_type', 'scheduled_date', 'status', 'priority', 'assigned_to']
    list_filter = ['status', 'priority', 'task_type']
    date_hierarchy = 'scheduled_date'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'asset_property' , 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status', 'category']
