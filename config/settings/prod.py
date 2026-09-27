import os

from .base import *  # noqa: F401,F403

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'example.com').split(',') if h.strip()]

DEBUG = False


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# PostgreSQL — БД проекта в продакшен .


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
    }
}
