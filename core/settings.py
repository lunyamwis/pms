import os
from pathlib import Path
import environ

# Initialize environ
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'ckeditor',
    'django_cleanup.apps.CleanupConfig',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    "drf_spectacular",


    'channels',

    # Local apps
    'accounts',
    'properties',
    'agents',
    'messaging',
    'bookings',
    'guests',
    'financials',
    'housekeeping',
    'integrations',
    'django_celery_beat',
]

JAZZMIN_SETTINGS = {
    "site_title": "LuxePMS Admin",
    "site_header": "LuxePMS",
    "site_brand": "LuxePMS",
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "Welcome to LuxePMS Administration",
    "copyright": "LuxePMS",
    "search_model": ["auth.User", "properties.Property"],
    "topmenu_links": [
        {"name": "Dashboard", "url": "/accounts/dashboard/", "permissions": ["auth.view_user"]},
        {"name": "Properties", "url": "/properties/", "new_window": False},
    ],
    "usermenu_links": [
        {"name": "Profile", "url": "/accounts/profile/", "icon": "fas fa-user"},
        {"name": "Support", "url": "https://github.com/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "accounts", "properties", "bookings", "guests", "financials", "housekeeping", "integrations"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.user": "fas fa-user-tie",
        "properties.property": "fas fa-building",
        "bookings.booking": "fas fa-calendar-check",
        "guests.guest": "fas fa-user-friends",
        "financials.cashbookentry": "fas fa-book",
        "financials.receipt": "fas fa-receipt",
        "housekeeping.cleaningtask": "fas fa-broom",
        "housekeeping.maintenancerequest": "fas fa-tools",
        "integrations.messagetemplate": "fas fa-envelope",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'accounts.middleware.SecurityMiddleware',
    'accounts.middleware.ActivityTrackingMiddleware',
]

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session Settings
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
            'core.context_processors.mapbox_token',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Channel layers for real-time functionality
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Mapbox configuration
MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', '')

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Authentication Settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# AllAuth settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Changed to optional for development
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_PASSWORD_MIN_LENGTH = 10
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True

# AllAuth URL Settings
ACCOUNT_LOGOUT_URL = '/accounts/logout/'
ACCOUNT_PASSWORD_CHANGE_URL = '/accounts/password/change/'
ACCOUNT_PASSWORD_RESET_URL = '/accounts/password/reset/'
ACCOUNT_EMAIL_CONFIRMATION_URL = '/accounts/confirm-email/'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'realestate_sessionid'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Custom forms and templates
ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm'
}

# Rate limiting settings
ACCOUNT_RATE_LIMITS = {
    # Five failed login attempts in 5 minutes
    "login_failed": "5/5m",
    # Three signup attempts per IP per day
    "signup": "3/d",
    # Five password reset attempts per day
    "password_reset": "5/d",
    # Two email changes per day
    "email_change": "2/d",
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.hostinger.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='noreply@crystalcodes.org')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='@Bigboy10men...')
DEFAULT_FROM_EMAIL = 'Real Estate <noreply@crystalcodes.org>'
SERVER_EMAIL = 'noreply@crystalcodes.org'
CONTACT_EMAIL = 'noreply@crystalcodes.org'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])

# CKEditor settings
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# === OTA & Communication Integrations ===
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

BOOKING_COM_USERNAME = os.environ.get('BOOKING_COM_USERNAME', '')
BOOKING_COM_PASSWORD = os.environ.get('BOOKING_COM_PASSWORD', '')

AIRBNB_CLIENT_ID = os.environ.get('AIRBNB_CLIENT_ID', '')
AIRBNB_CLIENT_SECRET = os.environ.get('AIRBNB_CLIENT_SECRET', '')

# === PMS Settings ===
PMS_COMPANY_NAME = os.environ.get('PMS_COMPANY_NAME', 'LuxePMS')
PMS_CURRENCY = os.environ.get('PMS_CURRENCY', 'KES')
PMS_CURRENCY_SYMBOL = os.environ.get('PMS_CURRENCY_SYMBOL', 'KSh')

# === Celery Beat Schedule ===
from celery.schedules import crontab

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {
    'sync-booking-com-every-15min': {
        'task': 'integrations.tasks.sync_all_booking_com',
        'schedule': crontab(minute='*/15'),
    },
    'sync-airbnb-every-15min': {
        'task': 'integrations.tasks.sync_all_airbnb',
        'schedule': crontab(minute='*/15'),
    },
    'send-pre-arrival-messages': {
        'task': 'integrations.tasks.send_pre_arrival_messages',
        'schedule': crontab(hour=9, minute=0),
    },
    'send-review-requests': {
        'task': 'integrations.tasks.send_pending_review_requests',
        'schedule': crontab(hour='*/2', minute=0),
    },
    'send-checkout-reminders': {
        'task': 'integrations.tasks.send_checkout_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
}
