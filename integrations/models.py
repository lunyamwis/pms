from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BookingComProperty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookingcom_properties')
    property = models.OneToOneField(
        'properties.Property', on_delete=models.CASCADE, related_name='bookingcom_config'
    )
    hotel_id = models.CharField(max_length=100)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=500)
    is_connected = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)
    auto_confirm = models.BooleanField(default=False)
    auto_reply_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking.com Property'
        verbose_name_plural = 'Booking.com Properties'

    def __str__(self):
        return f"{self.property} - Booking.com ({self.hotel_id})"


class AirbnbProperty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='airbnb_properties')
    property = models.OneToOneField(
        'properties.Property', on_delete=models.CASCADE, related_name='airbnb_config'
    )
    listing_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    is_connected = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)
    auto_confirm = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Airbnb Property'
        verbose_name_plural = 'Airbnb Properties'

    def __str__(self):
        return f"{self.property} - Airbnb ({self.listing_id})"


class WhatsAppConfig(models.Model):
    PROVIDER_CHOICES = [('twilio', 'Twilio'), ('meta_cloud', 'Meta Cloud API')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='whatsapp_configs')
    property = models.ForeignKey(
        'properties.Property', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='whatsapp_configs'
    )
    is_active = models.BooleanField(default=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='twilio')
    account_sid = models.CharField(max_length=200, blank=True)
    auth_token = models.CharField(max_length=200, blank=True)
    from_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"WhatsApp Config - {self.user} ({self.provider})"


class MessageTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('booking_confirmation', 'Booking Confirmation'),
        ('pre_arrival', 'Pre-Arrival Instructions'),
        ('check_in_instructions', 'Check-in Instructions'),
        ('checkout_reminder', 'Checkout Reminder'),
        ('review_request', 'Review Request'),
        ('receipt', 'Receipt'),
        ('payment_reminder', 'Payment Reminder'),
        ('welcome', 'Welcome Message'),
        ('farewell', 'Farewell Message'),
        ('general', 'General'),
    ]
    CHANNEL_CHOICES = [('whatsapp', 'WhatsApp'), ('email', 'Email'), ('both', 'Both')]

    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200, blank=True, help_text='Used for email subject')
    body = models.TextField(
        help_text='Use {{guest_name}}, {{check_in_date}}, {{check_out_date}}, {{property_name}}, {{booking_reference}}, {{total_amount}}, {{room_rate}}, {{wifi_name}}, {{wifi_password}}, {{access_instructions}}'
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='both')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['template_type', 'name']

    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"

    def render(self, context: dict) -> str:
        body = self.body
        for key, value in context.items():
            body = body.replace(f'{{{{{key}}}}}', str(value))
        return body


class IntegrationLog(models.Model):
    PLATFORM_CHOICES = [
        ('booking_com', 'Booking.com'), ('airbnb', 'Airbnb'),
        ('whatsapp', 'WhatsApp'), ('email', 'Email'),
    ]
    ACTION_CHOICES = [
        ('fetch_reservation', 'Fetch Reservation'),
        ('confirm_reservation', 'Confirm Reservation'),
        ('cancel_reservation', 'Cancel Reservation'),
        ('send_message', 'Send Message'),
        ('sync_availability', 'Sync Availability'),
        ('send_receipt', 'Send Receipt'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [('success', 'Success'), ('failed', 'Failed'), ('pending', 'Pending')]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='integration_logs'
    )
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} | {self.action} | {self.status} | {self.created_at}"
