from .base import *  # noqa: F401,F403
from .base import BASE_DIR

ALLOWED_HOSTS = ['*']
DEBUG = True


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# SQLite — БД проекта для разработки .


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
