import os
import sys

sys.path.append('/srv/django')

os.environ['DJANGO_SETTINGS_MODULE'] = 'lutrisweb.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

