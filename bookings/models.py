import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import datetime

User = get_user_model()


def generate_booking_reference():
    year = timezone.now().year
    count = Booking.objects.filter(created_at__year=year).count() + 1
    return f"BK-{year}-{count:04d}"


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_CHECKED_OUT = 'checked_out'
    STATUS_CANCELLED = 'cancelled'
    STATUS_NO_SHOW = 'no_show'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CHECKED_IN, 'Checked In'),
        (STATUS_CHECKED_OUT, 'Checked Out'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No Show'),
    ]

    SOURCE_DIRECT = 'direct'
    SOURCE_BOOKING_COM = 'booking_com'
    SOURCE_AIRBNB = 'airbnb'
    SOURCE_WALK_IN = 'walk_in'
    SOURCE_PHONE = 'phone'
    SOURCE_EMAIL = 'email'

    SOURCE_CHOICES = [
        (SOURCE_DIRECT, 'Direct'),
        (SOURCE_BOOKING_COM, 'Booking.com'),
        (SOURCE_AIRBNB, 'Airbnb'),
        (SOURCE_WALK_IN, 'Walk-in'),
        (SOURCE_PHONE, 'Phone'),
        (SOURCE_EMAIL, 'Email'),
    ]

    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    asset_property =  models.ForeignKey(
        'properties.Property', on_delete=models.PROTECT, related_name='bookings'
    )
    unit = models.ForeignKey(
        'properties.PropertyUnit', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bookings'
    )
    guest = models.ForeignKey(
        'guests.Guest', on_delete=models.PROTECT, related_name='bookings'
    )
    managed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_bookings'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_DIRECT)
    external_booking_id = models.CharField(max_length=100, blank=True)

    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_guests = models.PositiveIntegerField(default=1)
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)

    room_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_nights = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_paid = models.BooleanField(default=False)

    special_requests = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)

    confirmation_sent = models.BooleanField(default=False)
    pre_arrival_sent = models.BooleanField(default=False)
    review_request_sent = models.BooleanField(default=False)
    receipt_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            year = timezone.now().year
            count = Booking.objects.filter(created_at__year=year).count() + 1
            self.booking_reference = f"BK-{year}-{count:04d}"
        if self.check_in_date and self.check_out_date:
            delta = self.check_out_date - self.check_in_date
            self.total_nights = max(delta.days, 1)
        self.subtotal = self.room_rate * self.total_nights
        self.total_amount = (
            self.subtotal + self.cleaning_fee + self.service_fee +
            self.tax_amount - self.discount_amount
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.guest} ({self.check_in_date} to {self.check_out_date})"

    def get_absolute_url(self):
        return reverse('bookings:detail', kwargs={'pk': self.pk})

    @property
    def balance_due(self):
        paid = self.payments.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return self.total_amount - paid

    @property
    def is_upcoming(self):
        return self.check_in_date > timezone.now().date() and self.status in [
            self.STATUS_PENDING, self.STATUS_CONFIRMED
        ]

    @property
    def nights_until_checkin(self):
        delta = self.check_in_date - timezone.now().date()
        return delta.days

    @property
    def duration_nights(self):
        return self.total_nights

    def get_status_badge_class(self):
        mapping = {
            'pending': 'warning',
            'confirmed': 'primary',
            'checked_in': 'success',
            'checked_out': 'secondary',
            'cancelled': 'danger',
            'no_show': 'dark',
        }
        return mapping.get(self.status, 'secondary')

    def get_source_icon(self):
        mapping = {
            'booking_com': 'fa-building',
            'airbnb': 'fa-home',
            'direct': 'fa-user',
            'walk_in': 'fa-walking',
            'phone': 'fa-phone',
            'email': 'fa-envelope',
        }
        return mapping.get(self.source, 'fa-question')


class BookingPayment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('visa', 'Visa Card'),
        ('mastercard', 'Mastercard'),
        ('booking_com', 'Booking.com'),
        ('airbnb', 'Airbnb'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.amount} ({self.payment_method})"


class BookingMessage(models.Model):
    DIRECTION_CHOICES = [('inbound', 'Inbound'), ('outbound', 'Outbound')]
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('booking_com', 'Booking.com'),
        ('airbnb', 'Airbnb'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    sender_name = models.CharField(max_length=100)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    external_message_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.booking.booking_reference} [{self.channel}] {self.direction}"


class BookingNote(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField()
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.booking.booking_reference} by {self.author}"
