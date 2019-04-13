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

Module: Templates
=================

Internal template handling utilities.

"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from isomer.tool import log, error, debug


def format_template(template, content):
    """Render a given pystache template
    with given content"""

    import pystache

    result = u""
    try:
        result = pystache.render(template, content, string_encoding="utf-8")
    except (ValueError, KeyError) as e:
        log("Templating error:", e, type(e), exc=True, lvl=error)

    # pprint(result)
    return result


def format_template_file(filename, content):
    """Render a given pystache template file with given content"""

    with open(filename, "r") as f:
        template = f.read()
        if type(template) != str:
            template = template.decode("utf-8")

    return format_template(template, content)


def write_template_file(source, target, content):
    """Write a new file from a given pystache template file and content"""

    # print(formatTemplateFile(source, content))

    data = format_template_file(source, content)
    with open(target, "w") as f:
        for line in data:
            if type(line) != str:
                line = line.encode("utf-8")
            f.write(line)


def write_template(template, target, content):
    """Write a new file from a given pystache template file and content"""

    # print(formatTemplateFile(source, content))

    data = format_template(template, content)
    with open(target, "w") as f:
        for line in data:
            if type(line) != str:
                line = line.encode("utf-8")
            f.write(line)


def insert_nginx_service(definition):  # pragma: no cover
    """Insert a new nginx service definition"""

    config_file = "/etc/nginx/sites-available/isomer.conf"
    splitter = "### SERVICE DEFINITIONS ###"

    with open(config_file, "r") as f:
        old_config = "".join(f.readlines())

    log(old_config, pretty=True, lvl=debug)

    if definition in old_config:
        print("Service definition already inserted")
        return

    parts = old_config.split(splitter)
    log("Parts count:", len(parts), lvl=debug)
    if len(parts) != 3:
        print(
            "Nginx configuration seems to be changed and cannot be "
            "extended automatically anymore!"
        )
        log(parts, pretty=True, lvl=debug)
        return

    try:
        with open(config_file, "w") as f:
            f.write(parts[0])
            f.write(splitter + "\n")
            f.write(parts[1])
            for line in definition:
                f.write(line)
            f.write("\n    " + splitter)
            f.write(parts[2])
    except Exception as e:
        log(
            "Error during Nginx configuration extension:",
            type(e),
            e,
            lvl=error,
            exc=True,
        )
