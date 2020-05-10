FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG REQ_PATH=./config/requirements

ENV LC_ALL=C.UTF-8
ENV SECRET_KEY="somethissecret"
ENV DB_HOST="lutrisdb"
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.test"

RUN apt-get update && apt-get install -y sudo build-essential git curl python3 \
    python3-pip python3-dev imagemagick libxml2-dev libxslt1-dev libssl-dev libffi-dev \
    libpq-dev libxml2-dev libjpeg-dev
RUN curl -sL https://deb.nodesource.com/setup_13.x | bash -
RUN apt-get install -y nodejs

COPY $REQ_PATH/test.pip $REQ_PATH/base.pip /app/config/requirements/
WORKDIR /app/config/requirements
RUN pip3 install -r ./test.pip --exists-action=w

COPY ./*.json ./.bowerrc ./Gruntfile.js /app/
WORKDIR /app
RUN npm install -g bower grunt-cli
RUN npm install && npm run setup

CMD python3 manage.py runserver 0.0.0.0:8000