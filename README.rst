.. image:: https://travis-ci.org/isomeric/isomer.svg?branch=master
    :target: https://travis-ci.org/isomeric/isomer
    :alt: Build Status

.. image:: https://bestpractices.coreinfrastructure.org/projects/3650/badge
    :target: https://bestpractices.coreinfrastructure.org/projects/3650
    :alt: CII Best Practices

.. image:: https://coveralls.io/repos/isomeric/isomer/badge.svg
    :target: https://coveralls.io/r/isomeric/isomer
    :alt: Coverage

.. image:: https://requires.io/github/isomeric/isomer/requirements.svg?branch=master
    :target: https://requires.io/github/isomeric/isomer/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://img.shields.io/badge/IRC-%23hackerfleet%20on%20freenode-blue.svg
    :target: http://webchat.freenode.net/?randomnick=1&channels=hackerfleet&uio=d4>
    :alt: IRC Channel

.. image:: https://img.shields.io/badge/dynamic/json.svg?url=https://pypistats.org/api/packages/isomer/recent?mirrors=false&label=downloads&query=$.data.last_month&suffix=/month
    :target: https://pypistats.org/packages/isomer

.. image:: https://www.codetriage.com/isomeric/isomer/badges/users.svg
    :target: https://www.codetriage.com/isomeric/isomer
    :alt: Help via codetriage.com

.. |Contributor Covenant| image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
    :target: CODE_OF_CONDUCT.rst

.. image:: https://raw.githubusercontent.com/isomeric/isomer/master/docs/source/_static/logo_flat.png
    :target: https://github.com/isomeric/isomer
    :alt: Isomer Logo

◆ Isomer - Be Collaborative!
============================

**A collaborative and modular infrastructure for your data.**

Key features
------------

Why choose Isomer? Here's a short list of features of the Isomer Application Framework:

* **Modular** Expandable with integrated modules or build your own
* **Distributed** Focus on distributed requirements and features
* **Rapid** Develop your own applications rapidly
* **Reusability** Stop reinventing the wheel and integrate with proven modules
* **Cloud independent** Run nodes on your own infrastructure

Examples
--------

Here are some examples of what Isomer is being used for:

* **Geo Information** Use a sophisticated map to annotate and review
  geographical information
* **Vehicle support** Attach a sailyacht, your camper or pack one in your
  backpack to get spaceship-like Interfaces
* **Project planning** Project planning and tracking for collaborative teams
* **Multimedia mixing** AVIO is a suite for combining, mixing, controlling and
  playback of many, many independent media/stream formats

Much more incoming! We're eager to hear, what you're doing or planning to do!

⛁ Installation
==============

Please be wary of bugs and report strange things, thank you!

► Docker: Yes, please!
----------------------

If you just want to try it out or generally are happy with using docker, there
is no need to clone the repo, just download the docker compose file and get
everything from docker hub:

.. code-block:: sh

    wget https://github.com/isomeric/isomer/raw/master/docker/docker-compose-hub.yml
    docker-compose -f docker-compose-hub.yml up

See the `docker detail page
<https://isomer.readthedocs.io/en/latest/dev/system/docker.html#docker-details>`__
for more information.


☓ Docker: No, thanks..
----------------------

There is more than one way of installing Isomer, `see the detailed instructions
for those <https://isomer.readthedocs.io/en/latest/start/quick.html>`__.

If you intend to set up a development environment, `please follow the
development workflow instructions
<https://isomer.readthedocs.io/en/latest/dev/workflow.html>`__.

🕮 Documentation
================

The Isomer documentation is hosted at `ReadTheDocs.org <https://isomer.readthedocs.org>`__.

⊕ Modules
=========

Isomer is modular, so you can install what you need and leave out other
things.

A lot of the included modules are still Work in Progress, so help out, if
you're interested in a powerful - **cloud independent** - collaboration tool
suite.

♨ General modules
-----------------

These are 'official' Isomer modules. If you'd like to contribute your own,
ping community@isomer.eu, to get it added to the list.

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

⚓ Navigation (Hackerfleet) modules
-----------------------------------

Originating as a Hackerfleet project, we primarily focused on navigation tools,
early on, so these are currently the 'more usable' modules.

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
glasen         A "Glasenuhr", maritime clock for shift systems
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

☕ Work in progress
-------------------

-  Full GDAL based vector chart support (Currently only raster charts)
-  Dynamic Logbook
-  GRIB data (in charts)
-  Navigation aides, planning
-  Virtual/Augmented/eXtended Reality navigation
-  Datalog, automated navigational data exchange
-  Crew management, more safety tools
-  wireless crew network and general communications
-  audio/media system

⚯ Other 3rd party modules
-------------------------

============== ==============================================================
  Name           Description
============== ==============================================================
avio           Creative mixed media suite
library        Library management
polls          Tool for lightweight internet voting
garden         Garden automation tools
============== ==============================================================


↯ Bugs & Discussion
===================

Please research any bugs you find via our `Github issue tracker for
Isomer <https://github.com/isomeric/isomer/issues>`__ and report them,
if they're still unknown.

If you want to discuss distributed, opensource (or maritime) technology
in general incl. where we're heading, head over to one of our social
locations:

* `github.com/isomeric <https://github.com/isomeric>`__
* `Isomer Reddit <https://reddit.com/r/isomer>`__
* `Isomer Twitter <https://twitter.com/isomerframework>`__
* `Isomer Discord <https://discord.gg/T8MmQJd>`__
* `Isomer Matrix Channel <https://matrix.to/#/!vsbYAJRfIwQaCVmbRe:hackerfleet.eu?via=hackerfleet.eu&via=matrix.org>`__

We have other channels for the more maritime inclined:

* `github.com/hackerfleet <https://github.com/hackerfleet>`__
* `Hackerfleet Reddit <https://reddit.com/r/hackerfleet>`__
* `Hackerfleet Twitter <https://twitter.com/hackerfleet>`__
* `Hackerfleet Discord <https://discord.gg/2yHEk6S>`__
* `Hackerfleet Matrix Channel <https://matrix.to/#/!qQxCeUzrVeVKuEFwKT:hackerfleet.eu?via=hackerfleet.eu&via=matrix.org&via=synod.im>`__
* `Hackerfleet Facebook <https://www.facebook.com/Hackerfleet>`__
* `Hackerfleet G+ <https://plus.google.com/105528689027070271173>`__
* `IRC #hackerfleet on freenode <http://webchat.freenode.net/?randomnick=1&channels=hackerfleet&uio=d4>`__

♚ Contributors
==============

Please note that this project is released with a Contributor Code of Conduct.
By participating in this project you agree to abide by its terms.
Refer to `our COC <https://github.com/isomeric/isomer/CODE_OF_CONDUCT.rst>`__
(Contributor Covenant COC) for details.

Code
----

-  Heiko 'riot' Weinen riot@c-base.org
-  Johannes 'ijon' Rundfeldt ijon@c-base.org
-  Martin Ling
-  River 'anm' MacLeod
-  Sascha 'c_ascha' Behrendt c_ascha@c-base.org
-  `You? <mailto:community@isomer.eu?subject=Isomer Contributor Request>`_

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

© License
=========

Copyright (C) 2011-2020 Heiko 'riot' Weinen <riot@c-base.org> and others.

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


-- ⛵❤
