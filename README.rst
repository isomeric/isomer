.. image:: https://travis-ci.org/isomeric/isomer.png?branch=master
    :target: https://travis-ci.org/isomeric/isomer
    :alt: Build Status

.. image:: https://coveralls.io/repos/isomeric/isomer/badge.png
    :target: https://coveralls.io/r/isomeric/isomer
    :alt: Coverage

.. image:: https://requires.io/github/isomeric/isomer/requirements.png?branch=master
    :target: https://requires.io/github/isomeric/isomer/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://img.shields.io/badge/IRC-%23hackerfleet%20on%20freenode-blue.png
    :target: http://webchat.freenode.net/?randomnick=1&channels=hackerfleet&uio=d4>
    :alt: IRC Channel

.. image:: https://www.codetriage.com/isomeric/isomer/badges/users.png
    :target: https://www.codetriage.com/isomeric/isomer
    :alt: Help via codetriage.com

.. image:: https://img.shields.io/badge/dynamic/json.png?url=https://pypistats.org/api/packages/isomer/recent?mirrors=false&label=downloads&query=$.data.last_month&suffix=/month
    :target: https://pypistats.org/packages/isomer

Please be wary of bugs and report strange things, thank you!

Isomer - Be Collaborative!
==========================

**A collaborative and modular infrastructure for your data.**

* **Geo Information** Use a sophisticated map to annotate and review
  geographical information
* **Vehicle support** Attach a sailyacht, your camper or pack one in your
  backpack
* **Project planning** Issue tracking for collaborative teams
* **Modular** Expandable with integrated modules or build your own
* **Cloud independent** Run nodes on your own infrastructure

Much more incoming!

Installation
============

Docker: Yes, please!
^^^^^^^^^^^^^^^^^^^^

If you just want to try it out or generally are happy with using docker:

No need to clone the repo, just download the docker compose file and get
everything from docker hub:

.. code-block::

    wget https://github.com/isomeric/isomer/raw/master/docker/docker-compose-hub.yml
    docker-compose -f docker-compose-hub.yml up

See the `docker detail page
<https://isomer.readthedocs.io/en/latest/dev/system/docker.html#docker-details>`__
for more information.


Docker: No, thanks..
^^^^^^^^^^^^^^^^^^^^

There is more than one way of installing Isomer, `see the detailed instructions
for those <https://isomer.readthedocs.io/en/latest/start/quick.html>`__.

If you intend to set up a development environment, `please follow the
development workflow instructions
<https://isomer.readthedocs.io/en/latest/dev/workflow.html>`__.


Modules
=======

The system is modular, so you can install what you need and leave out other
things.

A lot of the included modules are still Work in Progress, so help out, if
you're interested in a powerful - **cloud independent** - collaboration tool
suite.

General modules
---------------

These are 'official' isomer modules. If you'd like to contribute your own,
ping riot@c-base.org, to get it added to the list.

Some (marked with \*) are work in progress and probably not really usable, yet.

Again, help is very welcome!

============== ==============================================================
  Name           Description
============== ==============================================================
automat*       Automation for non programmers
calc*          Integrated EtherCalc
calendar*      Calendar support
camera         Camera support
countables     Count arbitrary things
enrol          Enrollment/User account management
filemanager*   File management
heroic*        User achievements and badges
ldap*          LDAP user authorization
mail           E-Mail support
notifications* Channel independent user notification system
project        Project management tools
protocols      Miscellaneous communication protocols
sails          Web UI, compatible with all modern browsers (integrated)
sessions       Session chair module for planning conferences and similar
shareables     Shared resource blocking tool
simplechat     Very rudimentary integrated chat
transcript*    Meeting notes module
wiki           Etherpad + Wiki = awesomeness
============== ==============================================================

Navigation (Hackerfleet) modules
--------------------------------

We primarily focused on navigation tools, so these are currently the
'more usable' modules.
They are far from complete, see the WiP list below.

*Obligatory Warning*: **Do not use for navigational purposes!**
*Always have up to date paper maps and know how to use them!*

============== ==============================================================
  Name           Description
============== ==============================================================
alert          User alerting and notification system
anchor         Automatic anchor safety watcher
busrepeater    Tool to repeat navigation data bus frames to other media
comms          Communication package
dashboard      Dashboard information system
equipment      Equipment management
logbook        Displaying and manual logging of important (nautical) events
maps           (Offline) moving maps with shareable views/layers
mesh           Mesh networking
navdata        Navigational data module
nmea           NMEA-0183 Navigation and AIS data bus parser
nodestate      Node wide status system
robot          RC remote control unit
switchboard    Virtual switchboard
signal-k       Signal-K connector
webguides      Importer for skipperguide.de wiki content into the map
============== ==============================================================

Work in progress
----------------

-  Full GDAL based vector chart support (Currently only raster charts)
-  Dynamic Logbook
-  GRIB data (in charts)
-  Navigation aides, planning
-  Datalog, automated navigational data exchange
-  Crew management, more safety tools
-  wireless crew network and general communications

Other 3rd party modules
-----------------------

============== ==============================================================
  Name           Description
============== ==============================================================
avio           Creative mixed media suite
library        Library management
polls          Tool for lightweight internet voting
garden         Garden automation tools
============== ==============================================================


Bugs & Discussion
=================

Please research any bugs you find via our `Github issue tracker for
Isomer <https://github.com/isomeric/isomer/issues>`__ and report them,
if they're still unknown.

If you want to discuss distributed, opensource (or maritime) technology
in general incl. where we're heading, head over to our `Github discussion
forum <https://github.com/hackerfleet/discussion/issues>`__
...which is cleverly disguised as a Github issue tracker.

You can also find us here:

* `github.com/Hackerfleet <https://github.com/Hackerfleet>`__
* `reddit <https://reddit.com/r/hackerfleet>`__
* `Hackerfleet Twitter <https://twitter.com/hackerfleet>`__
* `Isomer Twitter <https://twitter.com/isomerframework>`__
* `Facebook <https://www.facebook.com/Hackerfleet>`__
* `soup.io <http://hackerfleet.soup.io/>`__
* `G+ <https://plus.google.com/105528689027070271173>`__
* `irc #hackerfleet on freenode <http://webchat.freenode.net/?randomnick=1&channels=hackerfleet&uio=d4>`__

.. note:: Please be patient when using IRC, responses might take a few hours!

Contributors
============

Code
----

-  Heiko 'riot' Weinen riot@c-base.org
-  Johannes 'ijon' Rundfeldt ijon@c-base.org
-  Martin Ling
-  River 'anm' MacLeod
-  Sascha 'c_ascha' Behrendt c_ascha@c-base.org
-  `You? <mailto:riot@c-base.org?subject=Isomer Contributor Request>`_

Assets
------

- Fabulous icons by iconmonstr.com, the noun project and Hackerfleet
  contributors

Support
-------

-  `c-base e.V. <https://c-base.org>`__ our home base, the spacestation below
   Berlin Mitte
-  Lassulus for hosting and nix expertise
-  `Jetbrains s.r.o <https://jetbrains.com>`__ for the opensource license of
   their ultimate IDE
-  `Github <https://github.com>`__ for hosting our code
-  `Gitlab <https://gitlab.com>`__ for hosting our code ;)
-  `Travis.CI <https://travis-ci.org>`__ for continuous integration services
-  `Docker Inc. <https://docker.com>`__ for providing containerization
   infrastructure
-  `ReadTheDocs.org <https://readthedocs.org>`__ for hosting our documentation
-  `BrowserStack <https://browserstack.com>`__ for cross device testing
   capabilities

License
=======

Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


-- :boat: :+1:
