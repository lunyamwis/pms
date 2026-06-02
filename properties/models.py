from django.db import models
from django.conf import settings
from django.utils.text import slugify
from ckeditor.fields import RichTextField

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condominium'),
        ('townhouse', 'Townhouse'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    )

    LISTING_TYPE_CHOICES = (
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
        ('lease', 'For Lease'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('off_market', 'Off Market'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = RichTextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in square feet")
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    garage = models.PositiveIntegerField(default=0)
    year_built = models.PositiveIntegerField(null=True, blank=True)

    # Location details
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    # Features and amenities
    features = models.ManyToManyField('PropertyFeature', blank=True)
    amenities = models.ManyToManyField('PropertyAmenity', blank=True)

    # Media
    main_image = models.ImageField(upload_to='properties/%Y/%m/%d/')
    video_url = models.URLField(blank=True)
    virtual_tour_url = models.URLField(blank=True)

    # Relationships
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_properties', limit_choices_to={'role__in': ['agent', 'seller']})
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_properties', limit_choices_to={'role': 'agent'})
    favorited_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='favorite_properties', blank=True)

    # Meta information
    is_featured = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    views_count = models.PositiveIntegerField(default=0)

    # Rental / STR fields
    rental_type = models.CharField(max_length=10, choices=[('str', 'Short-Term Rental'), ('ltr', 'Long-Term Rental'), ('both', 'Both')], default='str')
    is_managed = models.BooleanField(default=False)
    managed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_properties')
    airbnb_listing_url = models.URLField(blank=True)
    booking_com_url = models.URLField(blank=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    minimum_nights = models.PositiveIntegerField(default=1)
    maximum_nights = models.PositiveIntegerField(default=365)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weekly_discount = models.PositiveIntegerField(default=0)
    monthly_discount = models.PositiveIntegerField(default=0)
    house_rules = models.TextField(blank=True)
    wifi_name = models.CharField(max_length=100, blank=True)
    wifi_password = models.CharField(max_length=100, blank=True)
    access_instructions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'booking_property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def is_managed_by_agent(self):
        return self.agent is not None

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='properties/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.property.title}"

class PropertyFeature(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # For FontAwesome or similar icons

    def __str__(self):
        return self.name

class PropertyAmenity(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)  # For FontAwesome or similar icons

    class Meta:
        verbose_name_plural = 'Amenities'

    def __str__(self):
        return self.name

class PropertyReview(models.Model):
    booking_property = models.ForeignKey(Property, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='property_reviews', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('booking_property', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.get_full_name()} for {self.property.title}"

class PropertyUnit(models.Model):
    UNIT_TYPE_CHOICES = [
        ('room', 'Room'), ('apartment', 'Apartment'), ('studio', 'Studio'),
        ('suite', 'Suite'), ('villa', 'Villa'), ('cottage', 'Cottage'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'), ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'), ('reserved', 'Reserved'),
    ]

    booking_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='room')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    max_occupancy = models.PositiveIntegerField(default=2)
    num_beds = models.PositiveIntegerField(default=1)
    num_bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=1)
    floor_number = models.IntegerField(null=True, blank=True)
    size_sqft = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    has_kitchen = models.BooleanField(default=False)
    has_private_bathroom = models.BooleanField(default=True)
    amenities = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['booking_property', 'name']

    def __str__(self):
        return f"{self.property.title} - {self.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('properties:unit_detail', kwargs={'pk': self.pk})

    def is_available(self, check_in, check_out):
        from bookings.models import Booking
        overlapping = Booking.objects.filter(
            unit=self,
            status__in=['confirmed', 'checked_in'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
        ).exists()
        return not overlapping
