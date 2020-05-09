FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y sudo build-essential git curl python3 \
       python3-pip python3-dev imagemagick memcached libmemcached-dev \
       libxml2-dev libxslt1-dev libssl-dev libffi-dev

RUN curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs

WORKDIR /app
ADD . /app

ENV SECRET_KEY="somethissecret"
ENV DB_HOST="db"
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"
RUN /app/scripts/setup.sh
RUN cd /app/frontend/vue/ && npm install && npm run build:issues

RUN sh -c "touch templates/docs/installers.html"

EXPOSE 8000

CMD ["make", "run"]
