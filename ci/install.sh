#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
    pip3 install -r config/requirements/travis.pip
fi
