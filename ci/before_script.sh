#!/bin/bash
set -ex

if [ "${BUILD}" == "native" ]; then
  touch templates/docs/installers.html
fi
