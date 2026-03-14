"""Settings for CI (GitHub Actions)"""

import os

from lutrisweb.settings.base import *

SEND_EMAILS = False
DEBUG = False
AXES_ENABLED = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "lutris"),
        "USER": os.environ.get("POSTGRES_USER", "lutris"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "admin"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}
