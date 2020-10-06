#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2020 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

try:
    from setuptools import setup
except ImportError:
    # TODO: See if this can be sorted out by isomer.error.bail()
    print(
        "You will need to manually install python3 and python3-setuptools for "
        "your distribution"
    )
    sys.exit(50050)

ignore = [
    "/frontend/.idea",
    "/frontend/.git",
    "/frontend/node_modules",
    "/frontend/build",
    "/frontend/dist",
    "/frontend/src/components",
    "/docs/build",
    "__pycache__"
]
datafiles = []
manifestfiles = []


def prune(thing):
    for part in ignore:
        part = part[1:] if part.startswith("/") else part
        if part in thing:
            return True
    return False


def add_datafiles(*paths):
    with open("MANIFEST.in", "w") as manifest:
        for path in paths:
            files = []
            if os.path.isfile(path):
                manifest.write("include " + path + "\n")
                continue

            manifest.write("recursive-include " + path + " *\n")

            for root, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    datafile = os.path.join(root, filename)

                    if not prune(datafile):
                        files.append(datafile)
                        manifestfiles.append(datafile)

            datafiles.append((path, files))

        for part in ignore:
            if part.startswith("/"):
                manifest.write("prune " + part[1:] + "\n")
            else:
                manifest.write("global-exclude " + part + "/*\n")


add_datafiles("frontend", "docs", "locale")

with open("README.rst", "r") as f:
    readme = f.read()

setup(
    name="isomer",
    description="A decentralized application framework for humans and machines",
    author="Isomer Community",
    author_email="riot@c-base.org",
    maintainer="Isomer Community",
    maintainer_email="riot@c-base.org",
    url="https://isomeric.github.io",
    project_urls={
        "Documentation": "https://isomer.readthedocs.org/",
        "Funding": "https://isomeric.eu/donate",
        "Download": "https://isomeric.eu/download",
        "Source": "https://github.com/isomeric/isomer",
        "Tracker": "https://github.com/isomeric/isomer/issues",
    },
    license="GNU Affero General Public License v3",
    keywords="decentralized application framework",
    classifiers=[
        "Development Status :: 4 - Beta",  # Hmm.
        "Environment :: Web Environment",
        "Environment :: Other Environment",
        "Environment :: No Input/Output (Daemon)",
        # "Framework :: Isomer :: 1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Groupware",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: System :: Distributed Computing"
    ],
    packages=[
        "isomer",
        "isomer.database",
        "isomer.events",
        "isomer.misc",
        "isomer.provisions",
        "isomer.schemata",
        "isomer.tool",
        "isomer.ui"
    ],
    namespace_packages=["isomer"],
    long_description=readme,
    long_description_content_type="text/x-rst",
    dependency_links=[
        "https://github.com/ri0t/click-repl/archive/master.zip#egg=click-repl-0.1.3-ri0t",
        "https://github.com/ri0t/SecretColors/archive/master.zip#egg=SecretColors-1.2.0",
    ],
    install_requires=[
        "bcrypt>=3.2",
        "click-didyoumean>=0.0.3",
        "click-plugins>=1.1",
        "click-repl>=0.1.3-ri0t",
        "click>=7.1.2",
        "circuits",
        "distro>=1.5",
        "docutils>=0.16",
        "dpath>=2.0.1",
        "formal>=0.6.3",
        "gitpython>=3.1.8",
        "jsonschema>=3.2.0",
        "networkx",
        "numpy>=1.16.2",
        "prompt-toolkit>=2.0.10,<3",
        "pycountry>=20.7",
        "pyinotify>=0.9.6",
        "pypi-simple>=0.6.0",
        "pystache>=0.5.4",
        "pytz>=2020.1",
        "requests>=2.24.0",
        "spur>=0.3.21",
        "six>=1.15.0",
        "SecretColors>=1.2.0",
        "tomlkit>=0.7.0",
        "typing_extensions>=3.7.4.2",

    ],
    data_files=datafiles,
    entry_points="""[console_scripts]
    isomer=isomer.iso:main
    iso=isomer.iso:main

    [isomer.base]
    debugger=isomer.debugger:IsomerDebugger
    cli=isomer.debugger:CLI
    syslog=isomer.ui.syslog:Syslog
    maintenance=isomer.database.components:Maintenance
    backup=isomer.database.components:BackupManager

    [isomer.sails]
    auth=isomer.ui.auth:Authenticator
    clientmanager=isomer.ui.clientmanager:ClientManager
    objectmanager=isomer.ui.objectmanager:ObjectManager
    schemamanager=isomer.ui.schemamanager:SchemaManager
    tagmanager=isomer.ui.tagmanager:TagManager
    configurator=isomer.ui.configurator:Configurator
    store=isomer.ui.store.component:Store
    instanceinfo=isomer.ui.instance:InstanceInfo

    [isomer.schemata]
    systemconfig=isomer.schemata.system:Systemconfig
    client=isomer.schemata.client:Client
    profile=isomer.schemata.profile:Profile
    user=isomer.schemata.user:User
    logmessage=isomer.schemata.logmessage:LogMessage
    tag=isomer.schemata.tag:Tag
    theme=isomer.schemata.theme:Theme

    [isomer.provisions]
    system=isomer.provisions.system:provision
    user=isomer.provisions.user:provision
    """,
    use_scm_version={
        "write_to": "isomer/scm_version.py",
    },
    setup_requires=[
        "setuptools_scm"
    ],
    test_suite="tests.main.main",
)
