# -*- coding: utf-8 -*
import os


try:
    from . import local_settings
except ImportError:
    raise ImportError("You must create config file local_settings.py from template")


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from django.urls import reverse_lazy

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = local_settings.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = local_settings.DEBUG or False

ALLOWED_HOSTS = local_settings.ALLOWED_HOSTS

# required for django-guardian
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    'guardian.backends.ObjectPermissionBackend'
)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts_app',
    'photo_app',
    'abonapp',
    'tariff_app',
    'searchapp',
    'devapp',
    'mapapp',
    'statistics',
    'taskapp',
    'clientsideapp',
    'chatbot',
    'msg_app',
    'dialing_app',
    'guardian',
    'pinax_theme_bootstrap',
    'bootstrapform',
    'bootstrap3'

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'taskapp.context_proc.get_active_tasks_count',
                'global_context_processors.context_processor_additional_profile',
                'msg_app.context_processors.get_new_messages_count'
            ],
        },
    },
]

WSGI_APPLICATION = 'djing.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = local_settings.DATABASES


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

SESSION_COOKIE_HTTPONLY = True

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Simferopol'

USE_I18N = True

USE_L10N = False

USE_TZ = False

DEFAULT_FROM_EMAIL = local_settings.DEFAULT_FROM_EMAIL

# Maximum file size is 3.90625M
FILE_UPLOAD_MAX_MEMORY_SIZE = 4096000

# time to session live, 1 day
SESSION_COOKIE_AGE = 60 * 60 * 24


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
if DEBUG:
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)


# Example output: 16 september 2018
DATE_FORMAT = 'd E Y'

MEDIA_URL = '/media/'
if DEBUG:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_PICTURE = '/static/img/user_ava.gif'
AUTH_USER_MODEL = 'accounts_app.UserProfile'

LOGIN_URL = reverse_lazy('acc_app:login')
LOGIN_REDIRECT_URL = reverse_lazy('acc_app:profile')
LOGOUT_URL = reverse_lazy('acc_app:logout_link')

PAGINATION_ITEMS_PER_PAGE = local_settings.PAGINATION_ITEMS_PER_PAGE

PAY_SERV_ID = local_settings.PAY_SERV_ID
PAY_SECRET = local_settings.PAY_SECRET

DIALING_MEDIA = local_settings.DIALING_MEDIA

DHCP_TIMEOUT = local_settings.DHCP_TIMEOUT

DEFAULT_SNMP_PASSWORD = local_settings.DEFAULT_SNMP_PASSWORD

TELEGRAM_BOT_TOKEN = local_settings.TELEGRAM_BOT_TOKEN

TELEPHONE_REGEXP = r'^\+[7,8,9,3]\d{10,11}$'

ASTERISK_MANAGER_AUTH = local_settings.ASTERISK_MANAGER_AUTH

# Secret word for auth to api views by hash
API_AUTH_SECRET = local_settings.API_AUTH_SECRET

# Allowed subnet for api
API_AUTH_SUBNET = local_settings.API_AUTH_SUBNET
