Module setup
============

.. _module_setup:

Without installing or having any pre-installed modules, Isomer will not offer
much functionality.

Instance module installation
----------------------------

To install a module into your active default environment, use e.g.:

    ``iso -e current instance install-module -i -s github https://github.com/isomeric/isomer-enrol``

It is also possible to install a module you already downloaded:

    ``iso -e current instance install-module -i -s copy path/to/repo``

.. attention::

    Due to technical issues, you will need to rebuild the frontend for any
    environment with newly installed modules. This will be removed in future.