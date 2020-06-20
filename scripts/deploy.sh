#!/bin/bash

set -e

export DEPLOY_ENV=$1
export DEPLOY_HOST=$2

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

echo "Building lutrisweb"
docker-compose -f docker-compose.prod.yml build lutrisweb
echo "Building lutrisworker"
docker-compose -f docker-compose.prod.yml build lutrisworker
echo "Bringing Docker Compose up"
docker-compose -f docker-compose.prod.yml up -d
echo "Restarting NGinx"
docker-compose -f docker-compose.prod.yml restart lutrisnginx
