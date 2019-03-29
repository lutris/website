#!/bin/bash
set -ex

if [ "${BUILD}" == "native"]; then
    pip install -r config/requirements/devel.pip
fi
