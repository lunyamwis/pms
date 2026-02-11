from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.utils import timezone
from django.dispatch import receiver
from allauth.account.signals import email_confirmed
import pyotp

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('agent', 'Agent'),
    )

    email = models.EmailField(unique=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    bio = models.TextField(blank=True)
    
    # Contact preferences
    email_notifications = models.BooleanField(default=True)
    email_newsletter = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # Privacy settings
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    show_address = models.BooleanField(default=False)
    
    # Social media links
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    # Activity tracking
    last_active = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return self.get_full_name() or self.email
    
    def lock_account(self, duration_minutes=30):
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save()
    
    def unlock_account(self):
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def is_account_locked(self):
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
        self.save()
    
    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.save()
    
    def generate_2fa_secret(self):
        self.two_factor_secret = pyotp.random_base32()
        self.save()
        return self.two_factor_secret
    
    def verify_2fa_token(self, token):
        if not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token)
    
    def get_2fa_qr_url(self):
        if not self.two_factor_secret:
            return None
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(self.email, issuer_name="Real Estate")
    
    def update_last_active(self):
        self.last_active = timezone.now()
        self.save()
    
    def set_password(self, raw_password):
        super().set_password(raw_password)
        if raw_password:  # Only update timestamp if setting a real password
            self.password_changed_at = timezone.now()
    
    @property
    def requires_password_change(self):
        # Don't require password change for new users or if password was recently changed
        if not self.password_changed_at:
            return False
        # Require password change every 90 days
        days_since_change = (timezone.now() - self.password_changed_at).days
        return days_since_change >= 90
    
    @property
    def is_agent(self):
        return self.role == 'agent'
    
    @property
    def is_buyer(self):
        return self.role == 'buyer'
    
    @property
    def is_seller(self):
        return self.role == 'seller'

    def get_profile_picture_url(self):
        """Return URL of profile picture or default static image if missing or file absent."""
        from django.conf import settings
        default_url = settings.STATIC_URL + 'img/defaults/profile.png'
        if self.profile_picture:
            try:
                if self.profile_picture.storage.exists(self.profile_picture.name):
                    return self.profile_picture.url
            except Exception:
                pass
        return default_url

@receiver(email_confirmed)
def email_confirmed_handler(sender, request, email_address, **kwargs):
    """
    Signal handler to mark the user's email as verified when confirmed through allauth
    """
    user = email_address.user
    user.email_verified = True
    user.save()

class SavedSearch(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('any', 'Any Type'),
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condominium'),
        ('townhouse', 'Townhouse'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='any')
    min_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_bedrooms = models.PositiveIntegerField(null=True, blank=True)
    min_bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    min_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Saved Search'
        verbose_name_plural = 'Saved Searches'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.get_full_name()}"
