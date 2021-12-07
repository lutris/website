FROM node:14-buster
ARG DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN npm install

WORKDIR /app/frontend/vue
RUN npm install

WORKDIR /app
#CMD npm run build > /dev/null & cd /app/frontend/vue ; npm run build:issues-dev > /dev/null
CMD npm run watch
