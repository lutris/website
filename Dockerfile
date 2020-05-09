FROM ubuntu:20.04

ARG APP_USER=django
ARG DEBIAN_FRONTEND=noninteractive

ENV LC_ALL=C.UTF-8
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"

RUN apt-get update \
    && apt-get install -y sudo build-essential git curl python3 \
       python3-pip python3-dev imagemagick memcached libmemcached-dev \
       libxml2-dev libxslt1-dev libssl-dev libffi-dev npm libpq-dev locales \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://deb.nodesource.com/setup_13.x | sudo -E bash -
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs

# Install Node tools needed globally
RUN npm install -g bower grunt-cli

RUN useradd -ms /bin/bash -d /app ${APP_USER}
WORKDIR /app
ADD --chown=django:django . /app

RUN npm install
RUN npm run setup
USER ${APP_USER}:${APP_USER}
RUN cd /app/frontend/vue/ && npm install && npm run build:issues
RUN make client
RUN make docs

EXPOSE 8000

CMD ["make", "run"]
