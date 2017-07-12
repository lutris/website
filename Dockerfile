FROM ubuntu:16.04
MAINTAINER Joonatoona

WORKDIR /app
ADD . /app

ENV SECRET_KEY="somethissecret" DJANGO_SETTINGS_MODULE="lutrisweb.settings.local" USE_SQLITE=1
EXPOSE 8000

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y git curl python python-pip imagemagick memcached libmemcached-dev mercurial bzr
RUN /bin/bash /app/Docker/install.sh

CMD ["make", "run"]
