FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends sudo build-essential git curl ca-certificates
RUN curl -sL https://deb.nodesource.com/setup_13.x | bash -
RUN apt-get install -y nodejs
# RUN apt-get clean && rm -rf /var/lib/apt/lists/*
