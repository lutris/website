"""Production specific settings"""
from lutrisweb.settings.base import *  # noqa

DEBUG = False
MEDIA_URL = '//%s/media/' % DOMAIN_NAME
FILES_ROOT = '/srv/files'
FILES_URL = 'https://%s/files/' % DOMAIN_NAME

ALLOWED_HOSTS = ('.lutris.net', '0.0.0.0')

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

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_PORT = int(os.environ.get("EMAIL_HOST_PORT", 25))

STATICFILES_STORAGE = (
    'django.contrib.staticfiles.storage.CachedStaticFilesStorage'
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10/min',
    'user': '50/min'
}

STEAM_API_KEY = os.environ.get('STEAM_API_KEY')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
