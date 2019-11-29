.. _quick_install:

Quick Start Guide
=================

Docker
------

We're providing Docker images and composer files for quick and easy
installation.

The command to get the latest isomer is:

  ``docker-compose -f docker/docker-compose-hub.yml up``

This will spin up a database and Isomer itself.
If that worked, you should :ref:`head over to the setup <setup>`

If you run into trouble, check out the
:ref:`docker section of the developers manual <docker_details>` or try the
manual installation:

Manual Installation
===================

If you run into trouble or get any unexpected errors,
:ref:`try the complex installation procedure <complex_install>`, which details
all the automated bits and steps.

.. note::

    We're working on a detailed error handling system that includes links
    to online documentation and ad-hoc advice on how to fix problems.


Concepts
--------

To run an Isomer instance, it makes sense to get familiar with some terms:

=====================  ====================================================
Term                   Definition
=====================  ====================================================
Local Management       executing local commands to manage isomer systems
Management Tool        `iso` or `isomer` is the core application which
                       handles instance management and general setup
Instance               A single Isomer platform definition, providing
                       environments to run
Environment            The working parts of a single Isomer platform
                       i.e. the installed backend, modules and user data
Module                 Plug-In functionality for Isomer platforms
Remote Management      Using a local management tool to configure and
                       maintain remote hosted Isomer systems and instances
=====================  ====================================================

Install minimum dependency set
------------------------------

Please make sure, you have python3 as well as python3-setuptools installed.

Get Isomer
----------

Currently, getting Isomer via git is recommended. We are working on Python
packages, packages for multiple distributions as well as ready made images for
various embedded systems.

.. code-block:: sh

    git clone https://github.com/isomeric/isomer
    cd isomer
    git submodule update --init

Install Management Tool
-----------------------

The management tool's automatic installation currently only supports Debian
based systems.

.. tip::
   Feel free to contribute installation steps for other distros - that is
   mostly adapting the package manager and package names in
   isomer/tool/defaults.py

First, install the local management system:

.. code-block:: sh

    cd ~/src/isomer
    python3 setup.py install

Test the Tool
-------------

Now run

.. code-block:: sh

    iso version

to see if the tool installed correctly. It should print a few lines detailing
its version number and invocation place.

Set up the system
-----------------

To run securely and provide a robust upgrade and backup mechanism, your system
needs a few things set up:

* a user account for running instances
* some paths in `/var/lib/isomer`, `/var/local/isomer`, `/var/cache/isomer` and
* a configuration skeleton in `/etc/isomer`

Setting these up is done automatically by invoking

.. code-block:: sh

    iso system all

Create an Instance
------------------

Now you should be able to create and install your instance:

.. code-block:: sh

    iso instance create
    iso instance install

If that runs through successfully , you should :ref:`head over to the <setup>`.


Planned Installations
---------------------

* We're planning to offer ready-made SD card images for various embedded
  systems.
* A custom NixOS system is planned as well.
