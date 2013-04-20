import re
from os.path import join, dirname, abspath

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ENVIRONMENT = "dev"
THUMBNAIL_DEBUG = False

PROJECT_PATH = dirname(dirname(abspath(__file__)))

ADMINS = (
    ('Mathieu Comandon', 'strider@strycore.com'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(PROJECT_PATH, 'lutris.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = join(PROJECT_PATH, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = join(PROJECT_PATH, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    join(PROJECT_PATH, "common_static"),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'lessc {infile} {outfile}'),
)

SECRET_KEY = 'f8uok&amp;mchb26x5w6w+8nsa$+4zowxf09dayl3wk7(7l95+ppk1'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'lutrisweb.urls'
WSGI_APPLICATION = 'lutrisweb.wsgi.application'

TEMPLATE_DIRS = (
    join(PROJECT_PATH, "templates"),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    'django.core.context_processors.request',
    "django.contrib.messages.context_processors.messages",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'registration',
    'sorl.thumbnail',
    'compressor',
    'south',
    'django_jcrop',
    'mithril',
    'django_nose',

    'common',
    'games',
    'accounts',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SOUTH_TESTS_MIGRATE = False
LATEST_LUSTRIS_DEB = "http://lutris.net/releases/lutris_0.2.8_all.deb"

BANNER_SIZE = "184x69"
ICON_SIZE = "256x256"

ACCOUNT_ACTIVATION_DAYS = 3
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/user/login"
AUTH_PROFILE_MODULE = "accounts.Profile"

## Email
DEFAULT_FROM_EMAIL = "admin@lutris.net"
EMAIL_SUBJECT_PREFIX = "[Lutris] "

## Logging
IGNORABLE_404_URLS = (
    re.compile(r'^/games/install/'),
)
LOGGING_HANDLERS = ['file', 'mail_admins']
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
            'class': 'django.utils.log.NullHandler',
        },
        'mail_admins': {
            'level': 'DEBUG',
            'include_html': True,
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'lutrisweb.log'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': LOGGING_HANDLERS,
            'level': 'WARNING',
            'propagate': False,
        },
        'lutrisweb': {
            'handlers': LOGGING_HANDLERS,
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

try:
    from local_settings import *
except ImportError:
    pass

if ENVIRONMENT == "staging":
    MITHRIL_STRATEGY = 'common.strategy.PrivateBetaStrategy'
    MIDDLEWARE_CLASSES = (list(MIDDLEWARE_CLASSES)
                          + ['mithril.middleware.WhitelistMiddleware'])
