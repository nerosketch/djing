# -*- coding: utf-8 -*
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from django.core.urlresolvers import reverse_lazy

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!!!!!!!!!!!!!!!!!!!!!!!!YOUR SECRET KEY!!!!!!!!!!!!!!!!!!!!!!!!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


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
    'privatemessage',
    'abonapp',
    'tariff_app',
    'ip_pool',
    'searchapp',
    'devapp',
    'gmap',
    'statistics',
    'taskapp',
    'clientsideapp',
    'chatbot'
]

MIDDLEWARE_CLASSES = [
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
                'global_context_processors.context_processor_client_ipaddress',
                'taskapp.context_proc.get_active_tasks_count',
                'global_context_processors.context_processor_additional_profile'
            ],
        },
    },
]

WSGI_APPLICATION = 'djing.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'djingdb',
        'USER': 'USER',  # You can change the user name
        'PASSWORD': 'PASSWORD',  # You can change the password
        'HOST': 'localhost'
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Simferopol'

USE_I18N = True

USE_L10N = False

USE_TZ = True

DEFAULT_FROM_EMAIL = 'nerosketch@gmail.com'

# Максимальный загружаемый файл 3.90625M (кратно размеру блока диска 4kb, 4000 блоков)
FILE_UPLOAD_MAX_MEMORY_SIZE = 4096000

# Время жизни сессии, 1 сутки
SESSION_COOKIE_AGE = 60 * 60 * 24


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
if DEBUG:
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)


# Пример вывода: 16 сентября 2012
DATE_FORMAT = 'd E Y'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DEFAULT_PICTURE = '/static/images/default-avatar.png'
AUTH_USER_MODEL = 'accounts_app.UserProfile'

LOGIN_URL = reverse_lazy('acc_app:login')
LOGIN_REDIRECT_URL = reverse_lazy('acc_app:profile')
LOGOUT_URL = reverse_lazy('acc_app:logout_link')

PAGINATION_ITEMS_PER_PAGE=10
