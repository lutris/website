import os
from base import *  # noqa

if not os.environ.get('USE_SQLITE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'lutris',
            'USER': 'lutris',
            'PASSWORD': 'admin',
            'HOST': 'localhost',
        }
    }
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/lutris-emails'

STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
