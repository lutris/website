import os
from base import *  # noqa

DEBUG = False
MEDIA_URL = 'http://lutris.net/media/'

ALLOWED_HOSTS = ['.lutris.net', '.lutris.net.', ]

SECRET_KEY = os.environ['SECRET_KEY']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lutris',
        'USER': 'lutris',
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': 'localhost',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STEAM_API_KEY = os.environ['STEAM_API_KEY']
