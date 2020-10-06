Raspberry Pi
============


Updating and Environment Management
-----------------------------------

To automatically update a Raspberry Pi, you may use the Envrionment override GPIO
switch, which makes your instance boot into the other (updated) environment.

If something went wrong with the update, this allows you to return to your previous
(working and not updated) environment by removing/toggling the override GPIO switch.

.. note::
  More Information on configuring and using this will follow soon.

Swap
----
Since this machine doesn't have much RAM, don't forget to add a swap partition
or file.
