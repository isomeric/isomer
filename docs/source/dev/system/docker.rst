.. _docker_details:

Docker
======

As Docker allows easy deployment and usage of Isomer on many platforms, we
provide `ready-to-use images <https://hub.docker.com/r/isomeric/isomer>`_ on
a (currently) manual basis.

Setup
-----

The simplest way to get Isomer and a suitable database running is to run the
docker compose file:

.. code-block::

    docker-compose -f docker/docker-compose.yml up

This should grab all necessary software and spin up two machines, one
containing the database server and one with your Isomer instance.

Running the iso tool
--------------------

.. _isotool_docker:

To run the command via Docker compose:

.. code-block::

    docker-compose -f docker/docker-compose.yml run isomer iso db user

To run the iso tool inside your docker container without database access,
just use Docker's run command, e.g:

.. code-block::

    docker -i -t isomeric/isomer:latest run iso system status

To work with the database, you need to provide it an accessible server address:

.. code-block::

    docker -i -t isomeric/isomer:latest run iso --dbhost mydatabasehost:27017

.. note::
    Most of the command line options can also be supplied as environment
    variable, e.g. ``export ISOMER_LAUNCH_WEBADDRESS=0.0.0.0``

Platforms
---------

We provide amd64 and arm64 images built via buildkit and Docker's buildx
command.


Publishing
----------

Currently, we publish Docker images by hand, as building arm images on Docker-
Hub is not yet easily possible without hacks. This will change, as indicated in
their `bugtracker <https://github.com/docker/hub-feedback/issues/1874>`_.