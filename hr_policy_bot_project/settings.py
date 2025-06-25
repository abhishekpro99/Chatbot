#settings.py

import os
from pathlib import Path
import warnings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-please-change-me'

DEBUG = False

ALLOWED_HOSTS = ['*']

# Static files for Azure App Service
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # added
    'hr_policy_bot',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # added
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hr_policy_bot_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'hr_policy_bot_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings for Bot Framework (DirectLine, Teams, WebChat)
CORS_ALLOW_ALL_ORIGINS = True  # allow all temporarily; for prod use CORS_ALLOWED_ORIGINS

# Example safer config (optional):
# CORS_ALLOWED_ORIGINS = [
#     'https://hrpolicybot.azurewebsites.net',
#     'https://YOUR_WEBCHAT_CLIENT_URL',
# ]

# CSRF trusted origins (optional, for production security)
CSRF_TRUSTED_ORIGINS = [
    'https://hrpolicybot.azurewebsites.net',
]

# Logging to console (Azure App Service friendly)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Additional settings to avoid warnings when running aiohttp + Django in same process
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*Timezone support will be disabled.*')
os.environ['TZ'] = 'UTC'
