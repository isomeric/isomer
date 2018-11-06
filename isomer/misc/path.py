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

"""
"""

import os.path

INSTANCE = ""
ENVIRONMENT = None

locations = {
    'cache': '/var/cache/isomer/%s',
    'local': '/var/local/isomer/%s',
    'lib': '/var/lib/isomer/%s'
}


def set_instance(instance, environment):
    global INSTANCE
    global ENVIRONMENT

    INSTANCE = instance
    ENVIRONMENT = environment


def get_path(location, subfolder, ensure=False):
    """Return a normalized path for the running instance and environment"""

    path = locations[location] % INSTANCE
    if ENVIRONMENT is not None:
        path = os.path.join(path, ENVIRONMENT)
    path = os.path.join(path, subfolder)

    if ensure and not os.path.exists(path):
        os.makedirs(path)

    return path
