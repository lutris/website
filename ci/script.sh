#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
    export DJANGO=2.2.12
    export DJANGO_SETTINGS_MODULE='lutrisweb.settings.test'
    export SECRET_KEY="ThisIsMySecretThereAreOtherLikeThisButThisOneIsMine"
    export USE_SQLITE=1
    make db
    make test
elif [ "${BUILD}" == "docker" ]; then
    docker-compose build lutrisweb
    docker-compose run -e DJANGO_SETTINGS_MODULE='lutrisweb.settings.test' -w '/app' lutrisweb bash -c "touch templates/docs/installers.html && make db && make test"
fi
