FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y sudo build-essential git curl python3 \
    python3-pip python3-dev imagemagick memcached libmemcached-dev libxml2-dev libxslt1-dev libssl-dev libffi-dev \
    mercurial bzr libpq-dev libxml2-dev libjpeg-dev
ADD ./config/requirements/devel.pip /devel.pip
ADD ./config/requirements/base.pip /base.pip
RUN pip3 install -r /devel.pip --exists-action=w
RUN pip3 install Faker

RUN curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs

ENV SECRET_KEY="somethissecret"
ENV DB_HOST="db"
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"

ADD ./package.json /package.json
ADD ./package-lock.json /package-lock.json
ADD ./bower.json /bower.json
ADD ./.bowerrc /.bowerrc
ADD ./Gruntfile.js /Gruntfile.js
ADD ./polymer.json /polymer.json
RUN npm install -g bower grunt-cli
RUN npm install && npm run setup
ADD ./frontend/vue /frontend/vue
RUN mkdir /frontend/vue/static
WORKDIR /frontend/vue
RUN npm install && npm run build
