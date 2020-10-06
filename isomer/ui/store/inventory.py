# !/usr/bin/env python
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

"""

Module: Store
=============

Software inventory functionality

"""

import os
import base64
from docutils import core
from typing import Tuple

import requests
import zipfile

from urllib.parse import urljoin

from isomer.misc.std import std_datetime
from isomer.logger import isolog, debug
from isomer.ui.store import DEFAULT_STORE_URL

_STORE = {}


def log(*args, **kwargs):
    """Log as store emitter"""
    kwargs.update({"emitter": "STORE", "frame_ref": 2})
    isolog(*args, **kwargs)


def get_store(source=DEFAULT_STORE_URL,
              auth: Tuple[str, str] = None):
    """Return current store

    This function acts as cache for
    :func: `~isomer.store.inventory.populate_store`

    :param: source: Optionally, specify alternative store url
    :param: auth: Optional tuple containing username and password"""

    if _STORE == {}:
        return populate_store(source, auth)
    else:
        return _STORE


def inspect_wheel(wheel: str):
    """Inspeggtor reporting for duty!

    This thing opens up Python Eggs to analyze their content in an isomeric way.
    Some data pulled out is specific to isomer modules but could be used for general
    structures. Specifically, a `docs/README.rst` and a `docs/preview.png` is looked
    for.

    :param wheel: Filename of the python egg to inspect
    :return: Dictionary with
        `info` - content of docs/README.rst if found
        `preview` - content of docs/preview.png if found
        `date` - publishing date according to EGG-INFO/PKG-INFO timestamp
        `requires` - any required external python packages
    :rtype: dict
    """
    archive = zipfile.ZipFile(wheel)

    meta_name = os.path.basename(wheel).split("-py")[0] + ".dist-info/METADATA"

    try:
        info = archive.read("docs/README.rst").decode('utf-8')

        info = core.publish_parts(info, writer_name="html")["html_body"]
    except KeyError:
        info = "No information provided"

    try:
        preview = base64.b64encode(archive.read("docs/preview.png")).decode('utf-8')
    except KeyError:
        preview = ""

    pkg_info_info = archive.getinfo(meta_name)

    date = std_datetime(pkg_info_info.date_time)

    requires = []

    homepage = ""
    author = ""
    contact = ""
    package_license = ""

    try:
        lines = str(archive.read(meta_name), encoding="ascii").split("\n")

        for line in lines:
            if line.startswith("Home-page:"):
                homepage = line.split("Home-page: ")[1]
            if line.startswith("Author:"):
                author = line.split("Author: ")[1]
            if line.startswith("Author-email:"):
                contact = line.split("Author-email: ")[1]
            if line.startswith("License:"):
                package_license = line.split("License: ")[1]
            if line.startswith("Requires-Dist:"):
                req = line.split("Requires-Dist: ")[1]
                req = req.replace(" (", "").replace(")", "")
                requires.append(req)
    except KeyError:
        log("No metadata found")

    result = {
        'info': info,
        'preview': preview,
        'date': date,
        'requires': requires,
        'homepage': homepage,
        'author': author,
        'contact': contact,
        'license': package_license,
        'downloads': "-",
        'stars': "-"
    }
    log(result, pretty=True)

    return result


def populate_store(source=DEFAULT_STORE_URL,
                   auth: Tuple[str, str] = None):
    """Grab data from the isomer software store"""

    global _STORE

    log("Getting store information for", source, lvl=debug)

    url = urljoin(source, "/store")
    data = requests.get(url, auth=auth)
    index = data.json()

    _STORE = {
        'source': source,
        'auth': auth,
        'packages': index
    }

    return _STORE


def get_inventory(ctx):
    """Check local instance and its environments for installed modules"""

    instance_configuration = ctx.obj['instance_configuration']
    environment = instance_configuration['environment']
    environment_modules = instance_configuration['environments'][environment]['modules']

    instance_modules = instance_configuration['modules']

    log("Instance:", instance_modules, pretty=True)

    result = {
        'instance': instance_modules,
        'current': environment_modules
    }

    return result
