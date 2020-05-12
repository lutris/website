FROM node:14-buster

ARG DEBIAN_FRONTEND=noninteractive
ARG VUE_PATH=./frontend/vue

ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends sudo build-essential git curl ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./public/favicon.ico ./public/robots.txt /app/public/
COPY ./public/images /app/public/images/
COPY ./public/lightbox2 /app/public/lightbox2/
COPY ./*.json ./.bowerrc ./Gruntfile.js /app/
WORKDIR /app
RUN npm install -g bower grunt-cli
RUN npm install && npm run setup

COPY $VUE_PATH/*.json $VUE_PATH/.babelrc $VUE_PATH/.eslintignore $VUE_PATH/index.html $VUE_PATH/*.js /app/frontend/vue/
COPY $VUE_PATH/build /app/frontend/vue/build/
COPY $VUE_PATH/config /app/frontend/vue/config/
WORKDIR /app/frontend/vue
RUN npm install

WORKDIR /app
CMD npm run build ; npm run watch > /dev/null & cd /app/frontend/vue ; npm run build:issues-dev > /dev/null
