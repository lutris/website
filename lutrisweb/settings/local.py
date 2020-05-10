"""Settings specific to local development"""
import os
from lutrisweb.settings.base import *  # pylint: disable=wildcard-import,unused-wildcard-import

TEMPLATES[0]['OPTIONS']['debug'] = DEBUG


INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("POSTGRES_DB", "lutris"),
        'USER': os.environ.get("POSTGRES_USER", "lutris"),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', "admin"),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/lutris-emails'

STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
