from base import *  # noqa

SEND_EMAILS = False
DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
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
