Quick Start Guide
=================

.. _quick_install:

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

Install Management Tool
-----------------------

The management tool's automatic installation currently only supports Debian based systems.

.. tip::
   Feel free to contribute installation steps for other distros - that is mostly adapting the package manager
   and package names in isomer/tool/defaults.py

To use the automatic installation, get the source code (see :ref:`Getting the source <getting_source>`) if you
don't have it already, then invoke the tool with root permissions:

.. code-block:: sh

    sudo ./iso

If you run into trouble or get any unexpected errors, :ref:`try the complex installation procedure <complex_install>`.

Test the Tool
-------------

Now run

.. code-block:: sh

    iso version

to see if the tool installed correctly. It should print a few lines detailing its version number and invocation place.

Set up the system
-----------------

To run securely and provide a robust upgrade and backup mechanism, your system needs a few things set up:

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

Docker
------

.. attention::
    This image is currently in preparation, since a lot of things
    changed facilitating a new approach to Docker.

We're providing a Docker image for installation.

The command to get the current testing release is:

  ``docker run -i -t isomeric/isomer iso launch``


Planned Installations
---------------------

* We're planning to offer ready-made SD card images for various embedded systems.
* A custom NixOS system is planned as well.
