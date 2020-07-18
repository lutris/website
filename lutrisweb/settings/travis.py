from lutrisweb.settings.base import *  # noqa

SEND_EMAILS = False
DEBUG = False
AXES_ENABLED = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'lutris',
        'USER': 'lutris',
        'PASSWORD': 'admin',
        'HOST': 'lutrisdb',
        'PORT': '5432'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

INSTALLED_APPS += (
    'django_jenkins',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_pep8',
)

PROJECT_APPS = (
    'games',
    'accounts',
    'common'
)
