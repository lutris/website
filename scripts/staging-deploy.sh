#!/bin/bash

set -e

ROOT_DIR=/srv/staging
DJANGODIR=$ROOT_DIR/website/

source $ROOT_DIR/venv/bin/activate
export $(cat .env.staging | xargs)

cd $DJANGODIR
git pull

npm run build
npm run build-prod

./manage.py collectstatic --clear --noinput \
    --ignore less/test/* --ignore select2/docs/*

sudo systemctl stop gunicorn_staging
sleep 5
sudo systemctl start gunicorn_staging