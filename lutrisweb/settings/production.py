import os
from base import *  # noqa

DEBUG = False
MEDIA_URL = '//lutris.net/media/'
FILES_ROOT = '/srv/files'

ALLOWED_HOSTS = ['.lutris.net', '.lutris.net.', ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lutris',
        'USER': 'lutris',
        'PASSWORD': os.environ['DATABASE_PASSWORD'],
        'HOST': 'localhost',
    }
}

EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_USE_TLS = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STEAM_API_KEY = os.environ['STEAM_API_KEY']
