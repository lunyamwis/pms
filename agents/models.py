from django.db import models
from django.conf import settings
from django.urls import reverse

class Agent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent')
    license_number = models.CharField(max_length=50, unique=True)
    company_name = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(default=0)
    specializations = models.CharField(max_length=200, blank=True)
    service_areas = models.CharField(max_length=200, blank=True)
    languages = models.CharField(max_length=100, blank=True)
    
    # Contact information
    office_phone = models.CharField(max_length=20, blank=True)
    office_address = models.TextField(blank=True)
    
    # Professional details
    certifications = models.TextField(blank=True)
    awards = models.TextField(blank=True)
    
    # Notification preferences
    notify_new_inquiries = models.BooleanField(default=True)
    notify_property_updates = models.BooleanField(default=True)
    notify_client_messages = models.BooleanField(default=True)
    
    # Statistics
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_listings = models.PositiveIntegerField(default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company_name}"
    
    def get_absolute_url(self):
        return reverse('agents:detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def phone(self):
        return self.user.phone
    
    @property
    def profile_picture(self):
        return self.user.profile_picture
    
    @property
    def bio(self):
        return self.user.bio
