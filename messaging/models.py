from django.db import models
from django.conf import settings
from properties.models import Property

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id} - {', '.join(str(p) for p in self.participants.all())}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.subject}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('inquiry', 'Property Inquiry'),
        ('review', 'New Review'),
        ('property', 'Property Update'),
        ('system', 'System Notification')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} notification for {self.user}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class PropertyInquiry(models.Model):
    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both')
    ]
    
    INQUIRY_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_inquiries')
    message = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    preferred_contact_method = models.CharField(max_length=5, choices=CONTACT_CHOICES, default='email')
    status = models.CharField(max_length=20, choices=INQUIRY_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Property Inquiry'
        verbose_name_plural = 'Property Inquiries'
    
    def __str__(self):
        return f"Inquiry from {self.user} about {self.property}"
