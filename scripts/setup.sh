#!/bin/bash
#

set -e

if [ ! -d $HOME/.nvm/nvm.sh ]; then
    curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh | bash
    chmod 755 $HOME/.nvm/nvm.sh
fi
source $HOME/.nvm/nvm.sh
nvm install node
npm install -g bower grunt-cli
make setup
make deps
make sysdeps
make db
make client
make docs
pip3 install Faker
