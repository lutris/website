#!/bin/bash
#

set -e

npm install -g bower grunt-cli
make setup
make builddeps
make deps
make client
make docs
pip3 install Faker
