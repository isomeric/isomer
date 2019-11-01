# Docker Image for Isomer with single machine for Isomer and database
#
# This image essentially packages up Isomer along with mongodb into one single
# Docker Image/Container.
# If you want to run both seperately, please have a look at docker-compose.yml
#
# Usage Examples::
#
# To run your instance and see if the backend starts:
#     $ docker run -i -t isomeric/isomer /bin/bash -c "/etc/init.d/mongodb start && iso launch"
#
# To investigate problems on the docker container, i.e. get a shell:
#     $ docker run -i -t --name isomer-test-live -t isomeric/isomer
#
# VERSION: 1.2.0
#
# Last Updated: 20191014

FROM debian:experimental
MAINTAINER Heiko 'riot' Weinen <riot@c-base.org>

# Install dependencies

RUN echo "C.UTF-8" > /etc/locale.gen
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update
RUN apt-get -y install python3 python3-setuptools ca-certificates git

WORKDIR /home/isomer

# Copy repository

COPY . isomer
WORKDIR isomer

# Install Isomer

RUN python3 setup.py develop

RUN ./iso system -l -p Docker all

# Install instance

RUN ./iso instance create
RUN ./iso instance install -u /home/isomer/isomer --skip-provisions

RUN ./iso instance set web_port 8000

#  Services

EXPOSE 8000

# There is a frontend development server with hot reloading which can be started with
#   $ isomer/frontend/npm run start
# If you want to run the frontend development live server, uncomment this:
#
# EXPOSE 8081

