Instance Configuration
======================

.. _instance_configuration:

WiP

Environment Configuration
-------------------------

WiP

Component Configuration
=======================

.. _component_configuration:

Components start with a default configuration and can be configured via
command line tool, the configurator frontend module or environment variables.

Provisioning of components' configurations is not yet possible but maybe added
later.

Database
--------

WiP

Environment variables
---------------------

.. _component_environment_variables:

You can define environment variables in your launcher context to override
database and default settings. To do so, add variables of this naming scheme:

.. code-block::

    ISOMER_COMPONENT_{COMPONENTNAME}_{PROPERTY}_{SUBPROPERTY}={value}

To explain in more detail:

* Configuration of components always starts with ISOMER_COMPONENT_
* You can get a list of all the components' names with `iso config show`
* Since properties can be nested, replace any dots with `_` (underscores)
* Capitalize all parts of the name
* Values will be validated, so don't put text into number fields

Some caveats:

* If the overriden configuration property is different in the database,
  it will be overwritten there upon component initialization
* You cannot use complex structures like sub properties with nested properties
  as values, since there is no parser for them. Also, this would probably make
  things unnecessary complex, awkward and bug prone.