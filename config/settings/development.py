from .base import *

DEBUG = True

SECRET_KEY = env('SECRET_KEY', default='django-insecure-development-secret-key-!gestiflow!')

ALLOWED_HOSTS = ['*']

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True

# Database Configuration
# Primary Postgres 15 database in Docker/Prod, falls back to SQLite for local ease
if env('DATABASE_URL', default=None):
    DATABASES = {
        'default': env.db_url('DATABASE_URL')
    }
elif env('DB_HOST', default=None) and env('DB_HOST') != 'db':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='gestiflow_db'),
            'USER': env('DB_USER', default='gestiflow_user'),
            'PASSWORD': env('DB_PASSWORD', default='gestiflow_pass'),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Cache Configuration
# Redis 7 backend
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Celery Configurations
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/2')

# E-mail console backend for local testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Local storage for documents (simulating S3 bucket)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
