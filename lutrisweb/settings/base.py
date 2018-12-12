import os
from os.path import dirname, abspath

from celery.schedules import crontab


def media_directory(path):
    """Return absolute path to subdirectory of MEDIA_ROOT.
    The directory will be created if it doesn't exist.
    """
    abs_path = os.path.join(MEDIA_ROOT, path)
    if not os.path.isdir(abs_path):
        os.makedirs(abs_path)
    return abs_path


CLIENT_VERSION = "0.4.23"

DEBUG = False
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = False

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))

ADMINS = (
    ('Mathieu Comandon', 'strycore@gmail.com'),
)
MANAGERS = ADMINS
INTERNAL_IPS = ('127.0.0.1',)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'lutris.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

TIME_ZONE = 'Etc/UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "public"),
    os.path.join(BASE_DIR, "frontend/vue/dist"),
    os.path.join(BASE_DIR, "components"),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

FILES_ROOT = media_directory('files')
FILES_URL = 'http://localhost:8000/media/files/'

TOSEC_PATH = media_directory('tosec')
TOSEC_DAT_PATH = os.path.join(TOSEC_PATH)

# TheGamesDB directories
TGD_ROOT = media_directory('thegamesdb')
TGD_CLEAR_LOGO_PATH = media_directory('thegamesdb/clearlogo')
TGD_BANNER_PATH = media_directory('thegamesdb/banners')
TGD_SCREENSHOT_PATH = media_directory('thegamesdb/screenshot')
TGD_FANART_PATH = media_directory('thegamesdb/fanart')
TGD_LUTRIS_BANNER_PATH = media_directory('thegamesdb/lutris-banners')

SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme')

MIDDLEWARE = [
    # Caching disabled until proper invalidation is implemented
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
]

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
            ],
            'debug': False
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
    'rest_framework_swagger',
    'croppie',
    'crispy_forms',
    'django_select2',
    'markupfield',
    'django_openid_auth',
    'django_extensions',
    'reversion',

    'common',
    'platforms',
    'games',
    'bundles',
    'runners',
    'accounts',
    'tosec',
]

BANNER_SIZE = "184x69"
ICON_SIZE = "32x32"
ICON_LARGE_SIZE = "256x256"
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_COLORSPACE = "sRGB"

AUTH_USER_MODEL = 'accounts.User'
AUTH_PROFILE_MODULE = "accounts.Profile"
ACCOUNT_ACTIVATION_DAYS = 3
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/user/login/"
AUTHENTICATION_BACKENDS = (
    'django_openid_auth.auth.OpenIDBackend',
    'accounts.backends.SmarterModelBackend',
)
OPENID_SSO_SERVER_URL = 'http://steamcommunity.com/openid'

DISCOURSE_SSO_SECRET = os.environ.get('DISCOURSE_SSO_SECRET')
DISCOURSE_URL = 'https://forums.lutris.net'

DISCORD_URL = "https://discord.gg/C3uJjRD"
DISCORD_ISSUE_WEBHOOK_ID = os.environ.get('DISCORD_ISSUE_WEBHOOK_ID')
DISCORD_ISSUE_WEBHOOK_TOKEN = os.environ.get('DISCORD_ISSUE_WEBHOOK_TOKEN')
# Modify temporarily the session serializer because the json serializer in
# Django 1.6 can't serialize openid.yadis.manager.YadisServiceManager objects
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG

# Admin
GRAPPELLI_ADMIN_TITLE = "Lutris Administration"

# Select2
SELECT2_JS = '/static/js/select2.min.js'
SELECT2_CSS = '/static/css/select2.min.css'

# Email

try:
    SEND_EMAILS = bool(int(os.environ.get('SEND_EMAILS', '1')))
except ValueError:
    SEND_EMAILS = True
DEFAULT_FROM_EMAIL = "admin@lutris.net"
SERVER_EMAIL = "admin@lutris.net"
EMAIL_SUBJECT_PREFIX = "[Lutris] "

# Celery
CELERY_SEND_TASK_ERROR_EMAILS = True

CELERYBEAT_SCHEDULE = {
    'send-daily-mod-mail': {
        'task': 'accounts.tasks.daily_mod_mail',
        'schedule': crontab(hour=18, minute=0),
    },
    'delete-unchanged-forks': {
        'task': 'games.tasks.delete_unchanged_forks',
        'schedule': crontab(hour=17, minute=59)
    }
}
BROKER_URL = 'amqp://guest:guest@localhost//'
# API Keys
STEAM_API_KEY = "********************************"

# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
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
        'thegamesdb': DEFAULT_LOGGING_CONFIG
    }
}
