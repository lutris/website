#!/bin/bash

set -e

ENV=staging
WEBPACK=""

params=$(getopt -n $0 -o pw --long prod,webpack -- "$@")
eval set -- $params
while true ; do
    case "$1" in
        -p|--prod) ENV="prod"; shift ;;
        -w|--webpack) WEBPACK="1"; shift ;;
        *) shift; break ;;
    esac
done

ROOT_DIR=/srv/$ENV
DJANGODIR=$ROOT_DIR/website/

cd $DJANGODIR
git pull

source $ROOT_DIR/venv/bin/activate
export $(cat .env.$ENV | xargs)

if [[ "$WEBPACK" == "1" ]]; then
    npm run build
    npm run build-prod
fi

./manage.py collectstatic --clear --noinput --ignore less/test/* --ignore select2/docs/*
./manage.py migrate

sudo systemctl restart gunicorn_$ENV
