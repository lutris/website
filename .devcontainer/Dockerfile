ARG PYTHON_VER=3
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${PYTHON_VER}

ENV PYTHONUNBUFFERED 1

ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

RUN apt-get update \
    && apt install -y --no-install-recommends \
        imagemagick \
        libxml2-dev \
        libxslt1-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        libxml2-dev \
        libjpeg-dev \
        postgresql-client
