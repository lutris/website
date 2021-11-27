#!/bin/bash

set -e

cd /srv/staging/website
git pull
npm run build
npm run build-prod
sudo systemctl stop gunicorn_staging
sudo systemctl start gunicorn_staging