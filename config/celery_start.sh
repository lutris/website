#!/bin/bash

DJANGODIR=/srv/lutris/lutris.net
DJANGO_SETTINGS_MODULE=lutrisweb.settings.production

cd $DJANGODIR
source ../bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
source ../bin/envvars

exec ../bin/celery worker -A lutrisweb.celery.app -B --loglevel=INFO
