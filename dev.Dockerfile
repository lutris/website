FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG REQ_PATH=./config/requirements

ENV LC_ALL=C.UTF-8
ENV SECRET_KEY="somethissecret"
ENV DB_HOST="lutrisdb"
ENV POSTGRES_HOST="lutrisdb"
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"
ENV REDIS_HOST='lutriscache'

RUN apt-get update && apt-get install -y sudo build-essential git curl python3 \
    python3-pip python3-dev imagemagick libxml2-dev libxslt1-dev libssl-dev libffi-dev \
    libpq-dev libxml2-dev libjpeg-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY $REQ_PATH/devel.pip $REQ_PATH/base.pip /app/config/requirements/
WORKDIR /app/config/requirements
RUN pip3 install -r ./devel.pip --exists-action=w

WORKDIR /app
CMD python3 manage.py runserver 0.0.0.0:8000
