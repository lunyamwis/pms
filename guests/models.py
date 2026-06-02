from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class Guest(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'), ('female', 'Female'),
        ('other', 'Other'), ('prefer_not', 'Prefer not to say'),
    ]
    ID_TYPE_CHOICES = [
        ('passport', 'Passport'), ('national_id', 'National ID'),
        ('drivers_license', "Driver's License"), ('other', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    country_of_residence = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    language_preference = models.CharField(max_length=10, default='en')

    internal_rating = models.PositiveIntegerField(null=True, blank=True)
    is_vip = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)
    blacklist_reason = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_guests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Guest'
        verbose_name_plural = 'Guests'

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('guests:detail', kwargs={'pk': self.pk})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def total_bookings(self):
        return self.bookings.count()

    @property
    def total_spent(self):
        from django.db.models import Sum
        result = self.bookings.filter(
            status='checked_out'
        ).aggregate(total=Sum('total_amount'))
        return result['total'] or 0

    @property
    def last_stay(self):
        last = self.bookings.filter(status='checked_out').order_by('-check_out_date').first()
        return last.check_out_date if last else None

    @property
    def is_repeat_guest(self):
        return self.bookings.filter(status='checked_out').count() > 1

    @property
    def contact_number(self):
        return self.whatsapp_number or self.phone


class GuestDocument(models.Model):
    DOCUMENT_TYPES = [
        ('passport', 'Passport'), ('national_id', 'National ID'),
        ('drivers_license', "Driver's License"), ('visa', 'Visa'),
        ('other', 'Other'),
    ]

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='guest_documents/%Y/%m/')
    notes = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.guest.full_name} - {self.get_document_type_display()}"


class GuestReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    booking = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE, related_name='guest_review'
    )
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='reviews_received')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    overall_rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    cleanliness_rating = models.PositiveIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    communication_rating = models.PositiveIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rule_adherence_rating = models.PositiveIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comment = models.TextField(blank=True)
    is_recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review of {self.guest.full_name} - {self.overall_rating}/5"
