Documentation
*************

This section describes how to document your Isomer module properly, which includes
a module readme as well as store meta data.

More (and well integrated) documentation structures are work in progress.

Module Overview
===============

To add a descriptive, general documentation, add a README.rst to your module root
directory. This restructured text file serves as repository description on github/gitlab
and should contain at least a short description, setup instructions - if necessary - and
information on how to contribute or report bugs.

You can also add your license text once more, but if you already specified the license
in your `setup.py`, it will show up in the store overview.

Store description
=================

Developers are strongly encouraged to add an informational document for the Isomer store
module overview. This informs users on what the module provides and how it can help them,
as well as all necessary information to start working with the module.

To do this, a restructured text file needs to be added to the module's documentation
folder. In the store, this document will be shown right next to the module meta data to
people interested in extending the functionality of their Isomer instance.

The document should reside in `<module_root>/docs/README.rst` - if you want to
keep it simple, just link your repository readme:

.. code-block::

    cd <module_root>
    ln -s docs/README.rst README.rst

Store preview
-------------

Additionally, you can add a preview image (150x150px) to provide visual information.

To do so, add a square 150 pixel png file to the docs. The file should be called
`<module_root>/docs/preview.png`. Added benefit: You can use this file to add the same
picture on your repository readme, as the store will not download/render this image
again.
