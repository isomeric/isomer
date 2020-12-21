Provisions
==========

Provisions contain predefined data for Isomer data structures.
This ranges from necessary base data to (optional) additional resources.

Automatic Installation
======================

Isomer checks if required provisions have been installed on boot up and - if not -
tries to install them.

You can force provisioning via

.. code-block::

    iso --environment current environment install-provisions
