Modularity
**********

Modules
=======

Isomer modules are software packages to extend your installation's
functionality. They usually (but not always!) consist of:

- components
- events
- schemata
- provisions
- tool handlers
- frontend
- documentation


Components
----------

Components are the logic part of a module.

Events
------

Events are used to communicate requests between components.

Anonymous Events
^^^^^^^^^^^^^^^^

These are client side events without any authorization or identification
attached.

Authorized Events
^^^^^^^^^^^^^^^^^

After clients have logged in, they have access to a broad selection of so
called "authorized events". They have permissions and roles attached.
See :ref:`RBAC`

Internal Events
^^^^^^^^^^^^^^^

Console Events
^^^^^^^^^^^^^^


Schemata
--------

Schemata are used to specify (persistent) data structures and how they get
represented via forms.

Provisions
----------

Provisions are used when a module brings in additional data in the form of
persistent objects.

Tool handlers
-------------

To allow maintenance, modules can register tool commands. These are available
via the module section:

.. code-block:: sh

    iso module <command>

To get a list of all modules' commands, just do:

.. code-block:: sh

    iso module
