# Docker Image for Isomer
#
# This image essentially packages up Isomer and instantiates a default
# blank instance. This can be used to add further modules and customize.
#
# Since it doesn't make sense to run two services in one container, to run
# an additional compliant database, have a look at docker-compose.yml
#
# Usage Examples::
#
# To run your instance and see if the backend starts:
#     $ docker run -i -t isomeric/isomer iso --dbhost MYDATABASEHOST:27017 launch
#
# If everything built fine, point your browser to http://localhost:8000 to
# interact with the frontend.
#
# To investigate problems on the docker container, i.e. get a shell:
#     $ docker run -i -t isomeric/isomer iso instance info
#     $ docker run -i -t isomeric/isomer /bin/bash
#
# See
# https://isomer.readthedocs.io/en/latest/dev/system/docker.html#isotool-docker
# for more details.
#
# VERSION: 1.3.0
#
# Last Updated: 20191209

FROM debian:sid
MAINTAINER Heiko 'riot' Weinen <riot@c-base.org>

# Install dependencies

RUN echo "C.UTF-8" > /etc/locale.gen
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    enchant git apt-transport-https wget sudo gnupg virtualenv autoconf \
    mongodb-server ca-certificates build-essential libffi-dev libpng-dev \
    python3 python3-dev python3-pip python3-setuptools python3-enchant \
    python3-pil python3-nacl python3-spur python3-bson python3-pymongo \
    python3-cffi \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
  apt-get install -y --no-install-recommends --ignore-missing \
    python3-pymongo-ext python3-bson-ext \
    && rm -rf /var/lib/apt/lists/* || :

WORKDIR /home/isomer

# Copy requirements

COPY requirements-prod.txt requirements-doc.txt requirements.txt ./

# Install requirements

RUN pip3 install -r requirements-prod.txt

# Copy Isomer

COPY . isomer
WORKDIR isomer

RUN python3 setup.py develop

RUN ./iso system -l -p Docker all

# Install instance

RUN ./iso instance create
RUN ./iso instance install -s copy -u /home/isomer/isomer --skip-provisions

RUN ./iso instance set web_port 8000

#  Services

EXPOSE 8000

# There is a frontend development server with hot reloading which can be started with
#   $ isomer/frontend/npm run start
# If you want to run the frontend development live server, uncomment this:
#
# EXPOSE 8081

