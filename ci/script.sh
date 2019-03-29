#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
    make test
elif [ "${BUILD}" == "docker" ]; then
    docker-compose build
    docker-compose run web make test
fi
