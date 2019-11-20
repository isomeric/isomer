Instances
=========

Isomer runs so called instances to provide services to users.

Instance configuration and maintenance is handled by the `iso instance` command
group.

You can also edit the instance configuration in `/etc` by hand, but this
is not recommended.

If you do so, please validate the configuration after editing.

What is an Instance?
--------------------

An Isomer instance consists of two essential pieces:

* Metadata Configuration
* Environment system

Metadata Configuration
^^^^^^^^^^^^^^^^^^^^^^

* Lives in /etc/isomer/instances/<instancename>.conf
* Used to define properties like
  * General meta data (e.g. contact, name)
  * Database connectivity
  * Web interface settings (e.g. hostname, port, certificate)
  * System user configuration
  * Installed components and sources

Environment System
^^^^^^^^^^^^^^^^^^

An instance's actual software and aggregated things like user-uploaded data
resides in so called Environments.

Usually, an instance has at least two environments, a blue and a green one.
Next to these 'production' instances is the archive of older environments that
gets extended every time the instance is upgraded.

One of the driving factors behind this process is the required stability when
using Isomer in situations where software upgrades could potentially break
an instance without any means of repair available.
The implemented blue/green process allows downgrading to the earlier, uncom-
promised state.

Explanation of the Blue/Green process
-------------------------------------

* Instances have two default environments:
  * green
  * blue

* Only one environment per instance can be actively used at a time

* Upgrade/downgrade or backup restore actions will always be performed on the
  non active environment

* Both environments will exist in parallel for diagnostics and testing but
  control will be handed over to the newly installed environment for testing
  itself

* On success (and perhaps a confirmation of an administrator), the active
  environment is turned over to the running one

* Furthermore, the old archive gets updated and cleared out in preparation for
  another

* On errors (or perhaps a cancellation request of an administrator), the newly
  set up environment gets shut down, cleared and the old (working) environment
  gets activated and started again

.. _parallel_instances:

Parallel Instances
------------------

To allow running multiple Isomer systems on a single machine, multiple
instances can be set up to run in parallel.
