.. _Python: https://python.org
.. _MongoDb: https://mongodb.org/
.. _node: https://nodejs.org
.. _npm: https://npmjs.com

Requirements and Dependencies
=============================

Backend
-------

Isomer' backend has a few dependencies:

    - `Python`_: >= 3.3 (or possibly pypy >= 2.0)
    - Database: `MongoDb`_


.. note:: We have phased out Python 2.7 support.

A few more dependencies like nginx, and some python packages provided
per distribution are recommended, but not strictly necessary.

The Isomer Python package additionally installs a few pure Python libraries:

    - Circuits
    - Click and a few supporting packages
    - PyMongo
    - PyOpenSSL
    - PyStache
    - JSONSchema
    - DPath
    - DeepDiff

:Supported Platforms: Linux

:Supported Python Versions: 3.3, 3.4, 3.5, 3.6, 3.7

Frontend
--------

The frontend is built with

    - `node`_
    - `npm`_

and others. The detailed list can be found in frontend/package.json
after pulling the frontend git submodule.

.. todo:: Link backend deps