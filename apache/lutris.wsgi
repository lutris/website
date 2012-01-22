import os
import sys

sys.path.append('/home/strider/sites/djangoprojects')

os.environ['DJANGO_SETTINGS_MODULE'] = 'lutrisweb.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

