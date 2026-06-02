from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class HousekeepingStaff(models.Model):
    ROLE_CHOICES = [
        ('cleaner', 'Cleaner'),
        ('maintenance', 'Maintenance'),
        ('manager', 'Manager'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cleaner')
    is_active = models.BooleanField(default=True)
    properties = models.ManyToManyField(
        'properties.Property', blank=True, related_name='housekeeping_staff'
    )
    notes = models.TextField(blank=True)
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Housekeeping Staff'
        verbose_name_plural = 'Housekeeping Staff'

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class CleaningTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('checkout_clean', 'Post-Checkout Clean'),
        ('checkin_prep', 'Pre Check-in Preparation'),
        ('routine', 'Routine Clean'),
        ('deep_clean', 'Deep Clean'),
        ('inspection', 'Inspection'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')
    ]

    booking_property = models.ForeignKey(
        'properties.Property', on_delete=models.CASCADE, related_name='cleaning_tasks'
    )
    unit = models.ForeignKey(
        'properties.PropertyUnit', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cleaning_tasks'
    )
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cleaning_tasks'
    )
    assigned_to = models.ForeignKey(
        HousekeepingStaff, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='checkout_clean')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=60)
    actual_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    checklist = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    completion_photo = models.ImageField(upload_to='cleaning/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['scheduled_date', 'priority']

    def __str__(self):
        return f"{self.property} - {self.get_task_type_display()} - {self.scheduled_date}"

    def get_absolute_url(self):
        return reverse('housekeeping:task_detail', kwargs={'pk': self.pk})

    def get_priority_badge_class(self):
        return {'low': 'secondary', 'normal': 'info', 'high': 'warning', 'urgent': 'danger'}.get(self.priority, 'secondary')


class MaintenanceRequest(models.Model):
    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'), ('electrical', 'Electrical'),
        ('furniture', 'Furniture'), ('appliance', 'Appliance'),
        ('hvac', 'HVAC/AC'), ('structural', 'Structural'), ('other', 'Other'),
    ]
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')]
    STATUS_CHOICES = [
        ('open', 'Open'), ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed'),
    ]

    booking_property = models.ForeignKey(
        'properties.Property', on_delete=models.CASCADE, related_name='maintenance_requests'
    )
    unit = models.ForeignKey(
        'properties.PropertyUnit', on_delete=models.SET_NULL, null=True, blank=True
    )
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='maintenance_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    reported_by = models.CharField(max_length=100)
    assigned_to = models.ForeignKey(
        HousekeepingStaff, on_delete=models.SET_NULL, null=True, blank=True
    )
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.property} ({self.status})"


class RoomServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'),
    ]

    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.CASCADE, related_name='room_service_orders'
    )
    items = models.JSONField(default=list)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    handled_by = models.ForeignKey(HousekeepingStaff, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Room Service - {self.booking.booking_reference} ({self.status})"
