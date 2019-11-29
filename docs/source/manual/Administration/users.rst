User accounts
-------------

.. _user_accounts:

Without any accounts, you won't be able to use Isomer's frontend unless you
have the `isomer-enrol module <https://github.com/isomeric/isomer-enrol>`_
module installed and configured to accept self-registrations.

.. note::

    The isomer-enrol module provides methods for user self registration and
    administration in the frontend. It also provides password change
    functionality and other (customizable) user account infrastructure.

Normal users
^^^^^^^^^^^^

Normal users can use most of the functionality, but not change any vital
system parameters. Some functionality maybe restricted by the
:ref:`Role Based Access Control <rbac>` system, so you may need to adjust
roles, as well.

You can add a new user via:

    ``iso db user create-user``

It is also possible to provide the username on the command line:

    ``iso db user --username myuser create-user``

It will ask for a password, but you can supply this via:

    ``iso db user --username myuser --password mypass create-user``

Admin Account
^^^^^^^^^^^^^

You can add a new admin user via:

    ``iso db user create-admin``

The arguments for ``iso db user`` will be used.