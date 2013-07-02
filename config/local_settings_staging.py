DEBUG = False
ENVIRONMENT = "staging"
ALLOWED_HOSTS = ('dev.lutris.net',)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lutris_staging',
        'USER': 'lutris_staging',
        'PASSWORD': 'admin'
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
