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
Schema: System
==============

Contains
--------

System: Global systemwide settings


"""

from isomer.misc.std import std_salt
from isomer.logger import isolog, warn
from uuid import uuid4

SystemConfiguration = {
    "uuid": str(uuid4()),
    "salt": std_salt().decode('ascii'),
    "active": True,
    "name": "Default System Configuration",
    "description": "Default System description",
    "hostname": "localhost",
    "provisions": {"packages": ["user"]},
}


def provision_system_config(
    items, database_name, overwrite=False, clear=False, skip_user_check=False
):
    """Provision a basic system configuration"""

    from isomer.provisions.base import provisionList
    from isomer.database import objectmodels

    default_system_config_count = objectmodels["systemconfig"].count(
        {"name": "Default System Configuration"}
    )

    if default_system_config_count == 0 or (clear or overwrite):
        provisionList(
            [SystemConfiguration], "systemconfig", overwrite, clear, skip_user_check
        )
        isolog("Provisioning: System: Done.", emitter="PROVISIONS")
    else:
        isolog(
            "Default system configuration already present.",
            lvl=warn,
            emitter="PROVISIONS",
        )


provision = {
    "data": SystemConfiguration,
    "method": provision_system_config,
    "dependencies": "user",
}
