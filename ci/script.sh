#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
    export DJANGO=2.0.5
    export DJANGO_SETTINGS_MODULE='lutrisweb.settings.local'
    export SECRET_KEY="ThisIsMySecretThereAreOtherLikeThisButThisOneIsMine"
    export USE_SQLITE=1
    make test
elif [ "${BUILD}" == "docker" ]; then
    docker-compose build
    docker-compose run web make test
fi
