.. _setup:

Setup
=====

.. attention::

    If you're running Isomer via Docker, please note that you have to run the
    setup commands inside the docker container. See
    :ref:`the details for that <isotool_docker>`.

.. attention::

    If you're working with a virtual environment, do not forget to activate it
    first!

Modules
-------

You can install modules from local sources or github right now.

Installation
^^^^^^^^^^^^

    ``iso -e current instance install-module -i -s git URL``

Frontend rebuild
^^^^^^^^^^^^^^^^

After installing a module, you will have to rebuild the frontend:

    ``iso -e current environment install-frontend``

.. note::
    We're actively trying to eliminate this step, but currently it is not
    avoidable.

Admin Account
-------------

You can add a new admin user via:

    ``iso db user create-admin``

There is more :ref:`documentation about creating admins and users in the manual
section <user_accounts>`.