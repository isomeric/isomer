#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HFOS - Hackerfleet Operating System
# ===================================
# Copyright (C) 2011-2018 Heiko 'riot' Weinen <riot@c-base.org> and others.
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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from setuptools import setup
import os

# TODO:
# Classifiers
# Keywords
# download_url
# platform

ignore = [
    '/frontend/node_modules',
    '/frontend/build',
    '/frontend/src/components',
    '/docs/build',
    '__pycache__'
]
datafiles = []
manifestfiles = []


def prune(thing):
    for part in ignore:
        part = part[1:] if part.startswith('/') else part
        if part in thing:
            return True
    return False


def add_datafiles(*paths):
    with open('MANIFEST.in', 'w') as manifest:
        for path in paths:
            files = []
            manifest.write('recursive-include ' + path + ' *\n')

            for root, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    datafile = os.path.join(root, filename)

                    if not prune(datafile):
                        files.append(datafile)
                        manifestfiles.append(datafile)

            datafiles.append((path, files))

        for part in ignore:
            if part.startswith('/'):
                manifest.write('prune ' + part[1:] + '\n')
            else:
                manifest.write('global-exclude ' + part + '/*\n')


add_datafiles('frontend', 'docs')

setup(name="isomer",
      description="isomer",
      version="1.0.0",
      author="Isomer Community",
      author_email="riot@c-base.org",
      maintainer="Isomer Community",
      maintainer_email="riot@c-base.org",
      url="https://isomeric.github.io",
      license="GNU Affero General Public License v3",
      packages=['isomer',
                'isomer.schemata',
                'isomer.ui',
                'isomer.provisions'],
      namespace_packages=['isomer'],
      scripts=[
          'iso',
      ],
      long_description="""
Isomer - A distributed application framework
============================================

A modern, opensource approach to collaborative productivity.

This software package is supposed to run on your ship/car/plane/ufo's board
computer.
See https://github.com/isomeric/isomer""",
      dependency_links=[
          'https://github.com/Hackerfleet/warmongo/archive/master.zip#egg'
          '=warmongo-0.5.5.hf'
      ],
      install_requires=['circuits>=3.1',
                        'pymongo>=3.2',
                        'jsonschema==2.6.0',
                        'pystache>=0.5.4',
                        'click>=6.7.0',
                        'click-didyoumean>=0.0.3',
                        'click-repl>=0.1.2',
                        'click-plugins>=1.0.3',
                        'prompt-toolkit>=1.0.15',
                        'tomlkit>=0.4.6',
                        'spur>=0.3.20'
                        ],
      data_files=datafiles,
      entry_points="""[console_scripts]
    iso=iso:main

    [isomer.base]
    debugger=isomer.debugger:HFDebugger
    cli=isomer.debugger:CLI
    syslog=isomer.ui.syslog:Syslog
    maintenance=isomer.database:Maintenance
    backup=isomer.database:BackupManager

    [isomer.sails]
    auth=isomer.ui.auth:Authenticator
    clientmanager=isomer.ui.clientmanager:ClientManager
    objectmanager=isomer.ui.objectmanager:ObjectManager
    schemamanager=isomer.ui.schemamanager:SchemaManager
    tagmanager=isomer.ui.tagmanager:TagManager
    configurator=isomer.ui.configurator:Configurator

    [isomer.schemata]
    systemconfig=isomer.schemata.system:Systemconfig
    client=isomer.schemata.client:Client
    profile=isomer.schemata.profile:Profile
    user=isomer.schemata.user:User
    logmessage=isomer.schemata.logmessage:LogMessage
    tag=isomer.schemata.tag:Tag

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
