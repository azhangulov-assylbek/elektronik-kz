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


# HTTPS за reverse proxy (Caddy, см. Caddyfile): TLS завершается на Caddy,
# Django получает обычный HTTP и узнаёт исходную схему из X-Forwarded-Proto.
# Без этого request.is_secure() == False, и формы/логин падают с ошибкой CSRF.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Редирект http → https делает сам Caddy, в Django его не дублируем.
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS if host != '*' and not host.startswith('.')]


# Email: SMTP, если задан EMAIL_HOST, иначе письма пишутся в лог контейнера
# (как в development) — магазин работает и без настроенной почты.
if os.getenv('EMAIL_HOST'):
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': os.getenv('EMAIL_HOST'),
                'port': int(os.getenv('EMAIL_PORT', '587')),
                'username': os.getenv('EMAIL_HOST_USER', ''),
                'password': os.getenv('EMAIL_HOST_PASSWORD', ''),
                'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
                'use_ssl': os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true',
                'timeout': 10,
            },
        },
    }
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)  # noqa: F405
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', ADMIN_EMAIL)  # noqa: F405


# Логи в stdout контейнера — `docker compose logs web`.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
