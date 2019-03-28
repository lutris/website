FROM ubuntu:16.04
MAINTAINER Joonatoona

ENV LC_ALL=C.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y build-essential git curl python3 python3-pip python3-dev imagemagick memcached libmemcached-dev libxml2-dev libxslt1-dev libssl-dev libffi-dev mercurial bzr

WORKDIR /app
ADD . /app

ENV SECRET_KEY="somethissecret" DJANGO_SETTINGS_MODULE="lutrisweb.settings.local" USE_SQLITE=1
RUN /bin/bash /app/Docker/install.sh

EXPOSE 8000

CMD ["make", "run"]
