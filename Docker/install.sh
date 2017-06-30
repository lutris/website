#!/bin/bash

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh | bash
chmod 755 $HOME/.nvm/nvm.sh
source $HOME/.nvm/nvm.sh
nvm install node
npm install -g bower grunt-cli
git clone https://github.com/lutris/website.git /app
echo 'SECRET_KEY="jhkfghsldfkjghsldfh"' >> lutrisweb/settings/base.py
sed -i -e "s/sudo//g" Makefile
echo 'export DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"' >> ~/.bashrc
echo 'export USE_SQLITE=1' >> ~/.bashrc
export DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"
export USE_SQLITE=1
make setup
make sysdeps
make db
make client
make docs
pip install Faker
rm lutrisweb/settings/base.pyc
