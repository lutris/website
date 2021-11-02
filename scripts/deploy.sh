#!/bin/bash

set -e

export DEPLOY_ENV=${1:-"staging"}
export DEPLOY_HOST=${2:-"localhost"}

COMPOSE_OPTS="--compress"
if [[ "$3" == "--no-cache" ]]; then
    # Add --no-cache to build to disable cache and rebuild documentation.
    COMPOSE_OPTS="$COMPOSE_OPTS --no-cache"
fi

if [[ $DEPLOY_HOST ]]; then
    export DOCKER_HOST="ssh://$DEPLOY_HOST"
    echo "DOCKER_HOST set to $DOCKER_HOST"
fi
export COMPOSE_PROJECT_NAME=lutrisweb_$DEPLOY_ENV
if [[ $DEPLOY_ENV == "prod" ]]; then
    export POSTGRES_HOST_PORT=5435
    export HTTP_PORT=82
else
    export POSTGRES_HOST_PORT=5433
    export HTTP_PORT=81
fi

docker-compose --verbose -f docker-compose.prod.yml build $COMPOSE_OPTS lutrisweb
docker-compose --verbose -f docker-compose.prod.yml build $COMPOSE_OPTS lutrisworker

echo "Bringing Docker Compose up"
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml run lutrisweb ./manage.py migrate

echo "Restarting NGinx"
docker-compose -f docker-compose.prod.yml restart lutrisnginx
