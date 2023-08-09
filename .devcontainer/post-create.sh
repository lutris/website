#!/usr/bin/env bash

mkdir -p .vscode
cp .devcontainer/launch.json .vscode

pip install --upgrade pip
pip install -r config/requirements/devel.pip --exists-action=w

npm install
npm run build

./manage.py makemigrations
./manage.py migrate

# without docs tests will fail
make client
make docs

make test
