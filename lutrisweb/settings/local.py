from base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lutris',
        'USER': 'lutris',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
    }
}


STEAM_API_KEY = os.environ['STEAM_API_KEY']
