"""Base settings"""
import os
from os.path import dirname, abspath

from celery.schedules import crontab


def media_directory(path):
    """Return absolute path to subdirectory of MEDIA_ROOT.
    The directory will be created if it doesn't exist.
    """
    abs_path = os.path.join(MEDIA_ROOT, path)
    if not os.path.isdir(abs_path):
        try:
            os.makedirs(abs_path)
        except OSError:
            print(f"Failed to create {abs_path}")
    return abs_path


CLIENT_VERSION = "0.5.9.1"

DEBUG = True
THUMBNAIL_DEBUG = False

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))

ADMINS = (
    ('Mathieu Comandon', 'mathieucomandon@gmail.com'),
)
MANAGERS = ADMINS
INTERNAL_IPS = ('127.0.0.1',)

TIME_ZONE = 'Etc/UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Allow customization of domain
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "lutris.net")

ROOT_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:9527"
ALLOWED_HOSTS = (
    "0.0.0.0",
    "127.0.0.1",
    "localhost",
)

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "public"),
    os.path.join(BASE_DIR, "frontend/vue/dist")
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

FILES_ROOT = media_directory('files')
FILES_URL = f'{ROOT_URL}/media/files/'

TOSEC_PATH = media_directory('tosec')
TOSEC_DAT_PATH = TOSEC_PATH

GOG_LOGO_PATH = media_directory('gog-logos')
GOG_LUTRIS_LOGO_PATH = media_directory('gog-lutris-logos')

SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme')

MIDDLEWARE = [
    # Caching disabled until proper invalidation is implemented
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'axes.middleware.AxesMiddleware',
]
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'HTTP_X_REAL_IP',
    'REMOTE_ADDR',
]

AXES_FAILURE_LIMIT = 50

ROOT_URLCONF = 'lutrisweb.urls'
WSGI_APPLICATION = 'lutrisweb.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.discord_url",
                "common.context_processors.dashboard_url",
            ],
            'debug': DEBUG
        }
    }
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'sorl.thumbnail',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'rest_framework_swagger',
    'croppie',
    'crispy_forms',
    'django_select2',
    'markupfield',
    'django_openid_auth',
    'django_extensions',
    'reversion',
    'axes',

    'common',
    'platforms',
    'games',
    'bundles',
    'runners',
    'accounts',
    'tosec',
    'providers',
]

BANNER_SIZE = "184x69"
ICON_SIZE = "128x128"
ICON_LARGE_SIZE = "256x256"
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_COLORSPACE = "sRGB"

AUTH_USER_MODEL = 'accounts.User'
AUTH_PROFILE_MODULE = "accounts.Profile"
ACCOUNT_ACTIVATION_DAYS = 3
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/user/login"
AUTHENTICATION_BACKENDS = (
    'axes.backends.AxesBackend',
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.SmarterModelBackend',
)
OPENID_SSO_SERVER_URL = 'http://steamcommunity.com/openid'

DISCOURSE_SSO_SECRET = os.environ.get('DISCOURSE_SSO_SECRET')
DISCOURSE_URL = 'https://forums.lutris.net'

DISCORD_URL = "https://discordapp.com/invite/Pnt5CuY"
DISCORD_ISSUE_WEBHOOK_ID = os.environ.get('DISCORD_ISSUE_WEBHOOK_ID')
DISCORD_ISSUE_WEBHOOK_TOKEN = os.environ.get('DISCORD_ISSUE_WEBHOOK_TOKEN')
DISCORD_INSTALLER_WEBHOOK_ID = os.environ.get('DISCORD_INSTALLER_WEBHOOK_ID')
DISCORD_INSTALLER_WEBHOOK_TOKEN = os.environ.get('DISCORD_INSTALLER_WEBHOOK_TOKEN')

SPACES_ACCESS_KEY_ID = os.environ.get("SPACES_ACCESS_KEY_ID")
SPACES_ACCESS_KEY_SECRET = os.environ.get("SPACES_ACCESS_KEY_SECRET")

# Modify temporarily the session serializer because the json serializer in
# Django 1.6 can't serialize openid.yadis.manager.YadisServiceManager objects
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_FAIL_SILENTLY = not DEBUG

# Admin
GRAPPELLI_ADMIN_TITLE = "Lutris Administration"

# Select2 - bundled using webpack
SELECT2_JS = ''
SELECT2_CSS = ''

# Email


SEND_EMAILS = True
if os.environ.get('DJANGO_TESTS') == "1":
    SEND_EMAILS = False
    AXES_ENABLED = False

DEFAULT_FROM_EMAIL = "admin@lutris.net"
SERVER_EMAIL = "admin@lutris.net"
EMAIL_SUBJECT_PREFIX = "[Lutris] "

# Celery
CELERY_SEND_TASK_ERROR_EMAILS = True

CELERYBEAT_SCHEDULE = {
    'delete-unchanged-forks': {
        'task': 'games.tasks.delete_unchanged_forks',
        'schedule': crontab(minute=1)
    },
    'clear-orphan-versions': {
        'task': 'games.tasks.clear_orphan_versions',
        'schedule': crontab(minute=2)
    },
    'clear-orphan-revisions': {
        'task': 'games.tasks.clear_orphan_revisions',
        'schedule': crontab(minute=3)
    },
    'clear-spammers': {
        'task': 'accounts.tasks.clear_spammers',
        'schedule': crontab(minute=4)
    },
    'clean-installers': {
        'task': 'games.tasks.auto_process_installers',
        'schedule': crontab(minute=5)
    }
}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
# API Keys
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', 'NO_STEAM_API_KEY_SET')

if DEBUG:
    ANON_RATE = '99/second'
    USER_RATE = '99/second'
else:
    ANON_RATE = '4/second'
    USER_RATE = '6/second'
# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': ANON_RATE,
        'user': USER_RATE
    },
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 250,
}

# Shell Plus
SHELL_PLUS_DONT_LOAD = ['tosec']

SILENCED_SYSTEM_CHECKS = [
    'urls.W002',
]

# CORS configuration
CORS_ORIGIN_WHITELIST = (
    'http://localhost:9527',
    'http://0.0.0.0:9527',
    'https://dashboard.lutris.net',
)

# Logging
SEND_BROKEN_LINK_EMAILS = False
LOGGING_HANDLERS = ['file', 'mail_admins', 'console']
DEFAULT_LOGGING_CONFIG = {
    'handlers': LOGGING_HANDLERS,
    'level': 'DEBUG',
    'propagate': True,
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'include_html': True,
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'lutrisweb.log'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': LOGGING_HANDLERS,
            'propagate': True,
            'level': 'INFO',
        },
        'scripts': {
            'handlers': LOGGING_HANDLERS,
            'propagate': True,
            'level': 'DEBUG',
        },
        'factory': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': LOGGING_HANDLERS,
            'level': 'WARNING',
            'propagate': True,
        },
        'lutrisweb': DEFAULT_LOGGING_CONFIG,
        'accounts': DEFAULT_LOGGING_CONFIG,
        'common': DEFAULT_LOGGING_CONFIG,
        'games': DEFAULT_LOGGING_CONFIG,
        'platforms': DEFAULT_LOGGING_CONFIG,
        'bundles': DEFAULT_LOGGING_CONFIG,
        'runners': DEFAULT_LOGGING_CONFIG,
        'tosec': DEFAULT_LOGGING_CONFIG,
        'providers': DEFAULT_LOGGING_CONFIG,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': f"{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"
    },
}

CELERY_CACHE_BACKEND = 'default'
SELECT2_CACHE_BACKEND = 'default'
