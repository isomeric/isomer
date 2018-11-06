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

from tomlkit import loads, dumps
from tomlkit.exceptions import NonExistentKey
from tomlkit import document, table, nl, comment

from isomer.misc import std_now
from isomer.tool import log, error, debug


def write_configuration(filename, config):
    """Write the main system configuration"""

    try:
        with open(filename, 'w') as f:
            f.write(dumps(config))
        log('Instance configuration stored.', lvl=debug)
        return True
    except PermissionError:
        log('PermissionError: Could not write instance management configuration file', lvl=error)
        return False


def read_configuration(filename):
    """Read the main system configuration"""

    with open(filename, 'r') as f:
        config = loads(f.read())
        log('Instance configuration loaded.', lvl=debug)

    return config


tpl = document()
tpl.add(comment('Isomer Instance Management Configuration'))
tpl.add(comment('Created on %s' % std_now()))
tpl.add(nl())

meta = table()
meta.add('distribution', 'debian')
meta['distribution'].comment('Currently only debian supported')
meta.add('init', 'systemd')
meta['init'].comment('Currently only systemd supported')
meta.add('basepath', '/home/isomer/')

tpl.add('meta', meta)

defaults = table()
defaults.add('environment', 'blue')
defaults.add('loglevel', '30')
defaults.add('quiet', True)
defaults.add('verbose', False)
defaults.add('database_host', 'localhost')
defaults.add('database_port', 27017)
defaults.add('database_type', 'mongodb')
defaults.add('user', 'isomer')
defaults.add('group', 'isomer')
defaults.add('web_hostname', 'localhost')
defaults.add('web_port', 8055)
defaults.add('modules', [])

defaults['database_type'].comment('Currently only mongodb supported')
defaults.add('webserver', 'nginx')
defaults['webserver'].comment('Currently only nginx supported')
defaults.add('service_template', 'isomer.service')
defaults['service_template'].comment('Located in SOURCEROOT/dev/templates for now')

default_environment = table()
default_environment.add('version', '')
default_environment.add('old_version', '')
default_environment.add('database', '')
default_environment.add('installed', False)
default_environment.add('provisioned', False)
default_environment.add('migrated', False)
default_environment.add('tested', False)
default_environment.add('running', False)

environments = table()
blue = default_environment
green = default_environment

environments.add("blue", blue)
environments.add("green", green)

archive = table()

environments.add('archive', archive)

defaults.add("environments", environments)

tpl.add('defaults', defaults)

instances = table()
tpl.add('instances', instances)

configuration_template = tpl
