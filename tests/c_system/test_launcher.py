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

"""
Isomer - Backend

Test Isomer Launcher
====================



"""

from isomer.launcher import Core

args = {
    "insecure": False,
    "quiet": False,
    "dev": False,
    "web_port": 80,
    "web_address": "127.0.0.1",
    "web_hostnames": "localhost",
    "cert": None,
    "blacklist": [],
}


def test_launcher():
    """Tests if the Core Launcher can be instantiated"""

    # Use a non privileged port for testing, until that part can be removed
    # from Core

    instance_configuration = {
        "web_address": "127.0.0.1",
        "web_port": 80000,
        "web_certificate": "",
        "environment": "blue",
        "environments": {"blue": {"blacklist": []}},
    }
    core = Core("testing", instance_configuration, **args)

    assert type(core) == Core
