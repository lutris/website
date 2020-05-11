FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8
ENV DB_HOST="localhost"
ENV DJANGO_SETTINGS_MODULE="lutrisweb.settings.production"

ARG APP_USER=django
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends sudo build-essential git curl python3 python3-pip python3-dev \
                          imagemagick memcached libmemcached-dev libxml2-dev libxslt1-dev \
                          libssl-dev libffi-dev npm libpq-dev locales wget gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
RUN echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-6.x.list
RUN apt-get update && apt-get install -y metricbeat


RUN npm install -g bower grunt-cli
RUN useradd -ms /bin/bash -d /app django

ADD --chown=django:django . /app
WORKDIR /app

RUN pip3 install --no-cache-dir -r config/requirements/production.pip

USER ${APP_USER}:${APP_USER}
RUN npm install
RUN npm run setup
RUN cd /app/frontend/vue/ && npm install && npm run build:issues
RUN make client
RUN make docs

CMD ["scripts/gunicorn_start.sh"]
