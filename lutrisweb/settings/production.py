"""Production specific settings"""
# pylint: disable=wildcard-import,unused-wildcard-import
from lutrisweb.settings.base import *  # noqa

DEBUG = False
ROOT_URL = os.environ.get("LUTRIS_ROOT_URL", "https://lutris.net")
DASHBOARD_URL = "https://dashboard.lutris.net"
MEDIA_URL = f'//{DOMAIN_NAME}/media/'
FILES_ROOT =  os.environ.get("LUTRIS_FILES_ROOT", '/srv/files')
FILES_URL = f'https://{DOMAIN_NAME}/files/'

ALLOWED_HOSTS = os.environ.get(
    "LUTRIS_ALLOWED_HOSTS", ".lutris.net,.lutr.is,0.0.0.0,localhost"
).split(",")

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
    'django.contrib.staticfiles.storage.StaticFilesStorage'
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
