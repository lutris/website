DEBUG = False
ENVIRONMENT = "staging"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lutris_staging',
        'USER': 'lutris_staging',
        'PASSWORD': 'admin',
        'HOST': '',
        'PORT': '',
    }
}


