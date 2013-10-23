DEBUG = False
ENVIRONMENT = "staging"
ALLOWED_HOSTS = ('dev.lutris.net',)
SECRET_KEY = 'zaZeiwiejeto1zoo7iluH5beequai9ienie9aipoz4aih8ouJe7ON0kuche2ea5t'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lutris_staging',
        'USER': 'lutris_staging',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
    }
}


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mithril.middleware.WhitelistMiddleware'
)
MITHRIL_STRATEGY = 'common.strategy.PrivateBetaStrategy'
