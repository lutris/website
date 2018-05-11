FROM ubuntu:16.04
MAINTAINER Joonatoona

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y git curl python python-pip imagemagick memcached libmemcached-dev mercurial bzr

WORKDIR /app
ADD . /app

RUN /bin/bash /app/Docker/install.sh

ENV SECRET_KEY="somethissecret" DJANGO_SETTINGS_MODULE="lutrisweb.settings.local" USE_SQLITE=1
EXPOSE 8000

CMD ["make", "run"]
