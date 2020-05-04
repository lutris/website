#!/bin/bash

NAME="lutris"
PORT=8080
DJANGODIR=/app
USER=django
GROUP=django
NUM_WORKERS=9
DJANGO_WSGI_MODULE=lutrisweb.wsgi

echo "Starting $NAME as `whoami`"

cd $DJANGODIR
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

exec gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --user=$USER --group=$GROUP \
    --log-level=debug \
    --bind=127.0.0.1:$PORT

