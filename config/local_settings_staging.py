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
