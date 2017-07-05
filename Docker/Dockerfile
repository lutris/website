FROM ubuntu:16.04
MAINTAINER Joonatoona

WORKDIR /app
ADD ./install.sh /

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y git curl python python-pip imagemagick memcached libmemcached-dev mercurial bzr
RUN /bin/bash /install.sh

ENV SECRET_KEY "somethissecret"
ENV DJANGO_SETTINGS_MODULE "lutrisweb.settings.local"
ENV USE_SQLITE 1

CMD ["/bin/bash"]
