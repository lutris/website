#!/bin/bash

NAME="lutris"
DJANGODIR=/srv/lutris/lutris.net
SOCKFILE=/srv/lutris/run/gunicorn.sock
USER=django
GROUP=django
NUM_WORKERS=9
DJANGO_SETTINGS_MODULE=lutrisweb.settings.production
DJANGO_WSGI_MODULE=lutrisweb.wsgi

echo "Starting $NAME as `whoami`"

cd $DJANGODIR
source ../bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
export SECRET_KEY="the.secret.key"
export DATABASE_PASSWORD="the.password"
export STEAM_API_KEY="the.steam.key"

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --user=$USER --group=$GROUP \
    --log-level=debug \
    --bind=unix:$SOCKFILE

