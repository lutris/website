FROM node:14-buster

ARG DEBIAN_FRONTEND=noninteractive

ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends sudo build-essential git curl ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./*.json ./.bowerrc ./Gruntfile.js /app/
WORKDIR /app
RUN npm install -g bower grunt-cli
RUN npm install && npm run setup

WORKDIR /app/frontend/vue
