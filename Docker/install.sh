#!/bin/bash

curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh | bash
chmod 755 $HOME/.nvm/nvm.sh
source $HOME/.nvm/nvm.sh
nvm install node
npm install -g bower grunt-cli
sed -i -e "s/sudo//g" Makefile
make setup
make deps
make sysdeps
make db
make client
make docs
pip3 install Faker
