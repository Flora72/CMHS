from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-zu_@phyfzk+vi&xu&v26k9*zefpv!hy%j$!%gz^&l-dgnc1c6!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['cmhs.onrender.com', '127.0.0.1', 'alline-hirtellous-dario.ngrok-free.dev', '*']
SITE_ID = 1
# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cmhsApp.apps.CmhsappConfig',
    'accounts',
    'appointments',
    'payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CMHS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
         'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CMHS.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# DATABASES = {
#     'default' : {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'cmhs_db',
#         'USER': 'postgres',
#         'PASSWORD': '1234',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://cmhs_db_jjuu_user:sJe2TRZYJ7f1cNdL17sx6hSm0xqD7PZ0@dpg-d7l3mq1j2pic73cj66h0-a.oregon-postgres.render.com/cmhs_db_jjuu',
        conn_max_age=600
    )
}


USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/
# cmhs/settings.py

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_URL = 'static/'
AUTH_USER_MODEL = 'accounts.User'


# EMAIL CONFIGURATION
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')

# M-PESA CONFIGURATION
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')

JAZZMIN_SETTINGS = {
    # TITLE & HEADER
    "site_title": "Admin Dashboard",
    "site_header": "Chiromo MHS",
    "site_brand": "Online CMHS",
    "site_icon": "images/chiromo_logo.png",

    # LOGO CONFIGURATION
    "site_logo": "images/chiromo_logo.png",
    "login_logo": "images/chiromo_logo.png",
    "site_logo_classes": "img-fluid",

    # WELCOME & COPYRIGHT
    "welcome_sign": "Chiromo Mental Health System",
    "copyright": "Chiromo Hospital Group © 2026",

    # GLOBAL SEARCH
    "search_model": ["accounts.User", "appointments.Appointment", "payments.Transaction"],

    # TOP NAVBAR LINKS
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
        {"name": "Sign Out", "url": "admin:logout", "icon": "fas fa-sign-out-alt"},
    ],

    # SIDEBAR CONFIGURATION (FLATTENED)
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": ["appointments.SessionLog", "auth.Group"],


    "order_with_respect_to": [
        "accounts.User",
        "appointments.Appointment",
        "payments.Transaction",
        "sites.Site"
    ],

    # ICONS
    "icons": {
        "accounts.user": "fas fa-user-md",
        "appointments.appointment": "fas fa-calendar-check",
        "payments.transaction": "fas fa-file-invoice-dollar",
        "sites.site": "fas fa-globe",
    },

    # CUSTOM LINKS (Merged for Mobile Sign Out & PDF)
    "custom_links": {
        "accounts": [
            {
                "name": "Sign Out",
                "url": "/admin/logout/",
                "icon": "fas fa-power-off",
                "permissions": ["auth.view_user"]
            }
        ],
        "appointments": [
            {
                "name": "Download PDF Summary",
                "url": "export_appointments_pdf",
                "icon": "fas fa-file-pdf",
                "permissions": ["auth.view_user"]
            }
        ],
    },

    # UI HANDLERS
    "use_google_fonts": True,
    "show_ui_builder": False,
    "theme": "flatly",
    "changeform_format": "horizontal_tabs",
    "related_modal_active": True,
    "custom_js": "admin/js/tab_fix.js",
}

# UI TWEAKS FOR MOBILE RESPONSIVENESS
JAZZMIN_UI_TWEAKS = {
    "navbar_fixed": True,
    "sidebar_fixed": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_compact_style": True,
    "theme": "flatly",
    "navbar": "navbar-dark",
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "sidebar": "sidebar-dark-primary",
}
LOGOUT_REDIRECT_URL = '/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'