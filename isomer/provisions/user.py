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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""

Provisioning: User
==================

Contains
--------

Just creates a fulltext searchable index over the username field.


"""

from isomer.logger import isolog, warn

from uuid import uuid4

Users = [{"name": "System", "uuid": str(uuid4()), "roles": ["admin", "system", "crew"]}]


def provision_system_user(
    items, database_name, overwrite=False, clear=False, skip_user_check=False
):
    """Provision a system user"""

    from isomer.provisions.base import provisionList
    from isomer.database import objectmodels

    # TODO: Add a root user and make sure owner can access it later.
    # Setting up details and asking for a password here is not very useful,
    # since this process is usually run automated.

    if overwrite is True:
        isolog("Refusing to overwrite system user!", lvl=warn, emitter="PROVISIONS")
        overwrite = False

    system_user_count = objectmodels["user"].count({"name": "System"})
    if system_user_count == 0 or clear is False:
        provisionList(Users, "user", overwrite, clear, skip_user_check=True)
        isolog("Provisioning: Users: Done.", emitter="PROVISIONS")
    else:
        isolog("System user already present.", lvl=warn, emitter="PROVISIONS")


provision = {"data": Users, "method": provision_system_user}
