#!/bin/bash

set -e

ROOT_DIR=/srv/prod
DJANGODIR=$ROOT_DIR/website/

cd $DJANGODIR
git pull

source $ROOT_DIR/venv/bin/activate
export $(cat .env.prod | xargs)

if [[ "$1" == "--webpack" ]]; then
    npm run build
    npm run build-prod
    cd frontend/vue
    npm run build:issues
    cd ../..
fi

./manage.py collectstatic --clear --noinput \
    --ignore less/test/* --ignore select2/docs/*

sudo systemctl restart gunicorn_prod