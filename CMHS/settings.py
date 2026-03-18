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
DEBUG = False

ALLOWED_HOSTS = ['*', 'cmhs.onrender.com', 'alline-hirtellous-dario.ngrok-free.dev']

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
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
        default='postgresql://admin:7keu8lM4nOTjKw9T76FNe1o2WPiIrwBU@dpg-d6tgmu450q8c73ffl000-a.oregon-postgres.render.com/cmhs_db',
        conn_max_age=600
    )
}
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


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'perpymari@gmail.com'
EMAIL_HOST_PASSWORD = 'wmec oxyy ljen gvns'


# M-PESA CONFIGURATION (Sandbox)
MPESA_ENVIRONMENT = 'sandbox'
MPESA_CONSUMER_KEY = 'jXwNbMHUommAkHjNj9Az0it67zicDIyTVOGT0VFFAPA4y2hC'
MPESA_CONSUMER_SECRET = 'O9B480y6uxxkv50i0ZF2oQFflnkldlyeY9AfA8jc4fHGG5yBlM83730EoOdksB6T'
MPESA_SHORTCODE = '174379'
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
MPESA_INITIATOR_PASSWORD = 'YOUR_INITIATOR_PASSWORD'

JAZZMIN_SETTINGS = {

    "site_title": "Admin Dashboard",
    "site_header": "Chiromo MHS",
    "site_brand": "Online CMHS",

    # LOGO
    "site_logo": "images/chiromo_logo.png",
    "login_logo": "images/chiromo_logo.png",
    "site_logo_classes": "img-fluid",

    "welcome_sign": "Chiromo Mental Health System",
    "copyright": "Chiromo Hospital Group © 2026",
    "search_model": ["accounts.User", "appointments.Appointment", "payments.Transaction"],

    # TOP NAVBAR
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
        {"name": "Sign Out", "url": "#logout", "icon": "fas fa-sign-out-alt"},
    ],

    # SIDEBAR
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["accounts", "appointments", "payments"],

    "hide_models": [
        "appointments.SessionLog",
        "auth.Group",
    ],

    "icons": {
        "accounts.user": "fas fa-user-md",
        "appointments.appointment": "fas fa-calendar-check",
        "payments.transaction": "fas fa-file-invoice-dollar",
    },

    # SIDEBAR PDF LINK
    "custom_links": {
        "appointments": [
            {
                "name": "Download PDF Summary",
                "url": "export_appointments_pdf",
                "icon": "fas fa-file-pdf",
                "permissions": ["auth.view_user"]
            }
        ],
    },

    "custom_js": "admin/js/tab_fix.js",
    "use_google_fonts": True,
    "show_ui_builder": False,
    "theme": "flatly",
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TUNER = {
    "navbar": "navbar-navy",
    "sidebar": "sidebar-dark-navy",
    "accent": "accent-warning",
    "brand_colour": "navbar-navy",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "no_navbar_border": True,
}

LOGOUT_REDIRECT_URL = '/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'