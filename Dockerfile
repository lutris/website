FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y sudo build-essential git curl python3 python3-pip python3-dev imagemagick memcached libmemcached-dev libxml2-dev libxslt1-dev libssl-dev libffi-dev mercurial bzr

WORKDIR /app
ADD . /app

ENV SECRET_KEY="somethissecret" USE_SQLITE="$USE_SQLITE" DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"
RUN /app/scripts/setup.sh

RUN sh -c "touch templates/docs/installers.html"

EXPOSE 8000

CMD ["make", "run"]
