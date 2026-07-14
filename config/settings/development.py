from pathlib import Path
from decouple import config
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-for-petxpert')

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # Internal Apps
    'apps.core',
    'apps.accounts',
    'apps.pets',
    'apps.diagnosis.apps.DiagnosisConfig',
    'apps.veterinarians',
    'apps.appointments',
    'apps.consultations',
    'apps.prescriptions',
    'apps.notifications',
    'apps.payments',
    'apps.chat',
    'apps.marketplace',
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Karachi'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY' )
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='whsec_placeholder')

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
    # For production with Redis:
    # 'default': {
    #     'BACKEND': 'channels_redis.core.RedisChannelLayer',
    #     'CONFIG': {
    #         "hosts": [(config('REDIS_HOST', default='127.0.0.1'), int(config('REDIS_PORT', default=6379)))],
    #     },
    # },
}

# Chat Settings
CHAT_MAX_MESSAGE_LENGTH = 5000
CHAT_RATE_LIMIT = 20  # messages per 10 seconds
CHAT_PAGE_SIZE = 50

# AI Diagnosis Settings
GROQ_API_KEY = config('GROQ_API_KEY', default='')
ML_MODELS_DIR = BASE_DIR / 'ml_models'
ML_MODEL_VERSION = '1.0.0'

# Base URL for building absolute URIs (used for avatars in WebSocket messages)
BASE_URL = 'http://127.0.0.1:8000'

# ─── Django Unfold Admin Theme ───────────────────────────────────────────────
# Uses django-unfold to skin django.contrib.admin with PetXpert branding.
# All CRUD, permissions, filters, and inlines remain native Django Admin.
# See docs/ADMIN_CUSTOMIZATION.md for full documentation.

UNFOLD = {
    'SITE_TITLE': 'PetXpert Admin',
    'SITE_HEADER': 'PetXpert',
    'SITE_SUBHEADER': 'Healthcare & Marketplace Platform',
    'SITE_URL': '/',
    'SITE_SYMBOL': 'pets',
    'SITE_ICON': {
        'light': lambda request: static('images/petxpert_logo.png'),
        'dark': lambda request: static('images/petxpert_logo.png'),
    },
    'SITE_LOGO': {
        'light': lambda request: static('images/petxpert_logo.png'),
        'dark': lambda request: static('images/petxpert_logo.png'),
    },
    'SITE_FAVICONS': [
        {
            'rel': 'icon',
            'sizes': '32x32',
            'type': 'image/png',
            'href': lambda request: static('images/petxpert_logo.png'),
        },
    ],
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': True,
    'SHOW_BACK_BUTTON': True,
    'BORDER_RADIUS': '12px',
    'DASHBOARD_CALLBACK': 'apps.core.admin_dashboard.dashboard_callback',
    'ENVIRONMENT': 'apps.core.admin_dashboard.environment_callback',
    'LOGIN': {
        'image': lambda request: static('images/hero.png'),
        'redirect_after': lambda request: reverse_lazy('admin:index'),
    },
    'STYLES': [
        lambda request: static('admin/css/petxpert-admin.css'),
    ],
    'SCRIPTS': [
        lambda request: static('admin/js/petxpert-admin.js'),
    ],
    'COLORS': {
        'primary': {
            '50': '#eef3ff',
            '100': '#d4dcff',
            '200': '#b5c4ff',
            '300': '#8ba3ff',
            '400': '#5a7fe8',
            '500': '#1a56db',
            '600': '#003fb1',
            '700': '#003399',
            '800': '#002a7a',
            '900': '#001f5c',
            '950': '#00174d',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': True,
        'navigation': [
            {
                'title': _('Overview'),
                'separator': True,
                'collapsible': False,
                'items': [
                    {
                        'title': _('Dashboard'),
                        'icon': 'dashboard',
                        'link': reverse_lazy('admin:index'),
                    },
                    {
                        'title': _('View Site'),
                        'icon': 'open_in_new',
                        'link': '/',
                    },
                ],
            },
            {
                'title': _('Users & Accounts'),
                'collapsible': True,
                'items': [
                    {
                        'title': _('Users'),
                        'icon': 'people',
                        'link': reverse_lazy('admin:accounts_user_changelist'),
                    },
                    {
                        'title': _('Veterinarians'),
                        'icon': 'medical_services',
                        'link': reverse_lazy('admin:accounts_veterinarianprofile_changelist'),
                    },
                    {
                        'title': _('Sellers'),
                        'icon': 'storefront',
                        'link': reverse_lazy('admin:accounts_sellerprofile_changelist'),
                    },
                ],
            },
            {
                'title': _('Healthcare'),
                'collapsible': True,
                'items': [
                    {
                        'title': _('Pets'),
                        'icon': 'pets',
                        'link': reverse_lazy('admin:pets_pet_changelist'),
                    },
                    {
                        'title': _('Appointments'),
                        'icon': 'calendar_month',
                        'link': reverse_lazy('admin:appointments_appointment_changelist'),
                    },
                    {
                        'title': _('Prescriptions'),
                        'icon': 'medication',
                        'link': reverse_lazy('admin:prescriptions_prescription_changelist'),
                    },
                    {
                        'title': _('AI Diagnoses'),
                        'icon': 'biotech',
                        'link': reverse_lazy('admin:diagnosis_diagnosisrecord_changelist'),
                    },
                ],
            },
            {
                'title': _('Marketplace'),
                'collapsible': True,
                'items': [
                    {
                        'title': _('Products'),
                        'icon': 'inventory_2',
                        'link': reverse_lazy('admin:marketplace_product_changelist'),
                    },
                    {
                        'title': _('Orders'),
                        'icon': 'shopping_cart',
                        'link': reverse_lazy('admin:marketplace_order_changelist'),
                    },
                    {
                        'title': _('Categories'),
                        'icon': 'category',
                        'link': reverse_lazy('admin:marketplace_productcategory_changelist'),
                    },
                ],
            },
            {
                'title': _('System'),
                'collapsible': True,
                'items': [
                    {
                        'title': _('Payments'),
                        'icon': 'payments',
                        'link': reverse_lazy('admin:payments_payment_changelist'),
                    },
                    {
                        'title': _('Notifications'),
                        'icon': 'notifications',
                        'link': reverse_lazy('admin:notifications_notification_changelist'),
                    },
                    {
                        'title': _('Community Chat'),
                        'icon': 'forum',
                        'link': reverse_lazy('admin:chat_chatgroup_changelist'),
                    },
                ],
            },
        ],
    },
}
