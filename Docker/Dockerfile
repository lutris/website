FROM ubuntu
MAINTAINER Joonatoona

WORKDIR /app
ADD ./install.sh /

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y git curl python python-pip imagemagick memcached libmemcached-dev mercurial bzr
RUN /bin/bash /install.sh

CMD ["make", "run"]
