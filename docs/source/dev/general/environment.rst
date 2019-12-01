.. _Git: https://git-scm.com/

.. _environment:

Setting up a Isomer Development Environment
===========================================

This is the recommended way to setup a development environment for developing
the backend, frontend and modules of Isomer.

Getting Started
---------------

Here is a summary of the steps to your own development environment:

1. `Fork Isomer <https://github.com/isomeric/isomer#fork-destination-box>`_
   (*if you haven't done so already*)
2. Clone your forked repository using `Git`_
3. Install the local management tool
4. Install an Isomer development instance
5. Set up further development tools as desired

And you're done!

Setup
-----

.. attention::

    This part needs an overhaul, as it pretty much details the standard
    instance-base installation approach. This can be avoided by working
    with simple plain virtual environments and a few of the iso tool
    install commands.

The setup guide shall aid you in setting up a development environment for all
purposes and facettes of Isomer development. It is split up in a few parts
and a common basic installation.

Get the sourcecode
^^^^^^^^^^^^^^^^^^

After forking the repository, clone it to your local machine:

.. code-block:: sh

    git clone git@github.com:yourgithubaccount/isomer.git ~/src/isomer


Setting up a basic development Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First install the management tool:

.. code-block:: sh

    cd ~/src/isomer
    ./iso

This installs basic dependencies and installs the iso tool into your path.
Now, use it to set up system directories and users:

.. code-block:: sh

    iso system all

In theory, doing all steps is not required, but for safe measure, you should
probably at least run the dependency and path setup:

.. code-block:: sh

    iso system dependencies
    iso system paths

Create a new development instance (ignore the warning about a missing
default instance):

.. code-block:: sh

    iso -i development instance create

Install the development instance from your repository clone:

.. code-block:: sh

    iso -i development install -s copy -u ~/src/isomer

.. tip::

    You can use arguments like `--skip-frontend` to skip over various
    processes of the installation, if you intend to modify the installation
    by e.g. hand-installing a development module before these steps are
    applied.

Activate the newly installed environment:

.. code-block:: sh

    iso -i development turnover


Frontend Development
^^^^^^^^^^^^^^^^^^^^

Change to frontend directory:

.. code-block:: sh

    cd /var/lib/development/green/repository/frontend

and run the development webserver:

.. code-block:: sh

    npm run start

Now you can launch the frontend in your browser by going to
http://localhost:8081 To use other ports, either edit the webpack.config.js
file or launch the dev server directly:

.. code-block:: sh

    ./node_modules/.bin/webpack-dev-server --host localhost --port 8888

.. danger::

    Do not use the development server in production!

Module Development
^^^^^^^^^^^^^^^^^^

Activate environment:

.. code-block:: sh

    source /lib/isomer/development/green/venv/bin/activate

Install module for development:

.. code-block:: sh

    cd ~/src/isomer-module
    python setup.py develop

Currently, you'll need to restart (and possibly rebuild your frontend) your
instance to run with changes.

General Development
^^^^^^^^^^^^^^^^^^^

Stop instance if started via system service:

.. code-block:: sh

    systemctl stop isomer-development

.. tip::

    You can run production instances parallel to a development instance by
    configuring it as another instance and changing its web-port. See
    :ref:`Running parallel instances <parallel_instances>` for more
    information on that. If you only want to run it with a development
    webserver, this is not necessary.

Restart instance in console mode:

.. code-block:: sh

    cd /var/lib/isomer/development/green

    source ./venv/bin/activate

    iso --instance development --environment green --clog 10 launch

You should now see the startup process of your development instance log its
messages to your terminal.

.. tip::

    By typing `/help` + return on that console, you can read about the
    offered interactive command line commands.
