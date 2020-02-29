#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
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

"""
"""

import os.path

from isomer.tool import log, warn, debug

ETC_BASE_PATH = "/etc/isomer"

ETC_INSTANCE_PATH = os.path.join(ETC_BASE_PATH, "instances")
ETC_REMOTE_PATH = os.path.join(ETC_BASE_PATH, "remotes")
ETC_REMOTE_KEYS_PATH = os.path.join(ETC_BASE_PATH, "keys")

INSTANCE = ""
ENVIRONMENT = None
PREFIX = ""

locations = {
    "cache": "/var/cache/isomer/%s",
    "local": "/var/local/isomer/%s",
    "lib": "/var/lib/isomer/%s",
}


def set_etc_path(path):
    """Override the base path - dangerous! Only use for testing."""
    global ETC_BASE_PATH
    global ETC_INSTANCE_PATH
    global ETC_REMOTE_PATH
    global ETC_REMOTE_KEYS_PATH

    ETC_BASE_PATH = path

    ETC_INSTANCE_PATH = os.path.join(ETC_BASE_PATH, "instances")
    ETC_REMOTE_PATH = os.path.join(ETC_BASE_PATH, "remotes")
    ETC_REMOTE_KEYS_PATH = os.path.join(ETC_BASE_PATH, "keys")


def get_etc_path():
    """Get currently set configuration base path"""
    return ETC_BASE_PATH


def get_etc_instance_path():
    """Get currently set instance configurations base path, e.g.
    `/etc/isomer/instances/`"""
    return ETC_INSTANCE_PATH


def get_etc_remote_path():
    """Get currently set remote configurations base path"""
    return ETC_REMOTE_PATH


def get_etc_remote_keys_path():
    """Get currently set remote keys base path"""
    return ETC_REMOTE_KEYS_PATH


def get_log_path():
    """Get currently set logging base path"""
    if PREFIX not in (None, ""):
        path = os.path.join(PREFIX, "var", "log", "isomer")
    else:
        path = "/var/log/isomer"
    return path


def set_prefix(prefix):
    """Set a new base prefix (Caution!)"""
    global PREFIX

    PREFIX = prefix


def set_instance(instance, environment, prefix=None):
    """Sets the global instance and environment"""

    global INSTANCE
    global ENVIRONMENT
    global PREFIX

    INSTANCE = instance
    ENVIRONMENT = environment
    if prefix is not None:
        PREFIX = prefix
        log("Warning! Prefix is set:", PREFIX, lvl=warn)

    log("Setting Instance: %s and Environment: %s" % (INSTANCE, ENVIRONMENT), lvl=debug)


def get_path(location: str, subfolder: str, ensure: bool = False, instance: str = "",
             environment: str = ""):
    """Return a normalized path for the running instance and environment

    :param location: Either cache, local or lib - all reside in /var
    :param subfolder: Subfolder inside location
    :param ensure: Create the folder, if it doesn't exist and this parameter is True
    :param instance: Temporarily override to get at another instance's folder
    """

    if instance != "":
        instance_name = instance
    else:
        instance_name = INSTANCE

    if environment != "":
        environment_name = environment
    else:
        environment_name = ENVIRONMENT

    if PREFIX not in (None, ""):
        path = os.path.join(PREFIX, locations[location].lstrip("/") % instance_name)
    else:
        path = locations[location] % instance_name

    if environment_name is not None:
        path = os.path.join(path, str(environment_name))

    path = os.path.join(path, subfolder)
    path = path.rstrip("/")

    if ensure and not os.path.exists(path):
        os.makedirs(path)

    return path
