#!/bin/bash

set -e

export DEPLOY_ENV=$1
export DEPLOY_HOST=$2

# export DOCKER_HOST="ssh://$DEPLOY_HOST"
export COMPOSE_PROJECT_NAME=lutrisweb_$DEPLOY_ENV
if [[ $DEPLOY_ENV == "prod" ]]; then
    export POSTGRES_HOST_PORT=5435
    export HTTP_PORT=82
else
    export POSTGRES_HOST_PORT=5433
    export HTTP_PORT=81
fi

docker-compose --verbose -f docker-compose.prod.yml build lutrisweb
docker-compose --verbose -f docker-compose.prod.yml build lutrisworker
docker-compose --verbose -f docker-compose.prod.yml up -d
docker-compose --verbose -f docker-compose.prod.yml restart lutrisnginx
