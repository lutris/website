#!/bin/bash

set -e

ROOT_DIR=/srv/staging
DJANGODIR=$ROOT_DIR/website/

cd $DJANGODIR
git pull

source $ROOT_DIR/venv/bin/activate
export $(cat .env.staging | xargs)

if [[ "$1" == "--webpack" ]]; then
    npm run build
    npm run build-prod
fi

./manage.py collectstatic --clear --noinput \
    --ignore less/test/* --ignore select2/docs/*

sudo systemctl restart gunicorn_staging