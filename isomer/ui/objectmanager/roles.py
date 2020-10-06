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

Module: objectmanager.roles
===========================

RBAC (role based access control) support functionality for objects


"""

from isomer.component import handler
from isomer.database import objectmodels
from isomer.events.objectmanager import remove_role, add_role
from isomer.logger import error
from isomer.ui.objectmanager.crud import CrudOperations


class RoleOperations(CrudOperations):
    """Adds RBAC (role based access control) support functionality"""

    @handler(remove_role)
    def remove_role(self, event):
        """Remove a role from one or many objects' permissions"""

        schema = event.data.get("schema", None)
        uuid = event.data.get("uuid", None)
        action = event.data.get("action", None)
        role = event.data.get("role", None)

        if schema is None or uuid is None or action is None or role is None:
            self.log("Invalid request, arguments missing:", event.data, lvl=error)
            return

        user = event.user

        if not isinstance(uuid, list):
            uuid = [uuid]

        for item in uuid:
            obj = objectmodels[schema].find_one({"uuid": item})

            if not self._check_permissions(user, "write", obj):
                self.log("Revoking role not possible due to insufficient permissions.")
                return

            self.log("Removing role", role, "of", action, "on", schema, ":", item)
            try:
                obj.perms[action].remove(role)
                obj.save()
            except ValueError:
                self.log(
                    "Could not remove role, it is not existing:",
                    role,
                    action,
                    schema,
                    ":",
                    item,
                )

    @handler(add_role)
    def add_role(self, event):
        """Add a role to one or many objects' permissions"""

        schema = event.data.get("schema", None)
        uuid = event.data.get("uuid", None)
        action = event.data.get("action", None)
        role = event.data.get("role", None)

        if schema is None or uuid is None or action is None or role is None:
            self.log("Invalid request, arguments missing:", event.data, lvl=error)
            return

        user = event.user

        if not isinstance(uuid, list):
            uuid = [uuid]

        for item in uuid:
            obj = objectmodels[schema].find_one({"uuid": item})

            if not self._check_permissions(user, "write", obj):
                self.log("Adding role not possible due to insufficient permissions.")
                return

            self.log("Appending role", role, "of", action, "on", schema, ":", item)
            if role not in obj.perms[action]:
                obj.perms[action].append(role)
                obj.save()
            else:
                self.log("Role already present, not adding")
