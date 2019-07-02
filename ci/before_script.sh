#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
    touch templates/docs/installers.html
elif [ "${BUILD}" == "docker" ]; then
    sudo service postgresql stop
fi
