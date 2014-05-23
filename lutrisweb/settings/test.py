import os
from base import *  # noqa

DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

if not os.environ.get('NOCOVER'):
    NOSE_ARGS = (
        "--with-xcoverage", "--xcoverage-file=coverage.xml",
        "--with-xunit", "--xunit-file=nosetests.xml",
        "--cover-erase",
        "--cover-package=games",
        "--cover-package=accounts",
        "--cover-package=common",
    )
