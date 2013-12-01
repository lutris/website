DEBUG = False
ALLOWED_HOSTS = ('lutris.net', 'www.lutris.net', 'api.lutris.net')

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lutris',
        'USER': 'lutris',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STEAM_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
