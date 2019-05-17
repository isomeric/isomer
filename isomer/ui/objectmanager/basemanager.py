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

Module objectmanager.basemanager
================================

Basic object management functionality and component set up.

"""

from isomer.component import ConfigurableComponent
from isomer.database import objectmodels
from isomer.schemastore import schemastore

from isomer.events.client import send
from isomer.logger import verbose, warn, error


class ObjectBaseManager(ConfigurableComponent):
    """
    Handles object requests and updates.
    """

    channel = "isomer-web"

    configprops = {}

    def __init__(self, *args):
        super(ObjectBaseManager, self).__init__("OM", *args)

        self.subscriptions = {}

        self.log("Started")

    def _check_permissions(self, subject, action, obj):
        # self.log('Roles of user:', subject.account.roles, lvl=verbose)

        if "perms" not in obj._fields:
            if "admin" in subject.account.roles:
                # self.log('Access to administrative object granted', lvl=verbose)
                return True
            else:
                # self.log('Access to administrative object failed', lvl=verbose)
                return False

        if "owner" in obj.perms[action]:
            try:
                if subject.uuid == obj.owner:
                    # self.log('Access granted via ownership', lvl=verbose)
                    return True
            except AttributeError as e:
                self.log(
                    "Schema has ownership permission but no owner:",
                    obj._schema["name"],
                    lvl=verbose,
                )
        for role in subject.account.roles:
            if role in obj.perms[action]:
                # self.log('Access granted', lvl=verbose)
                return True

        self.log("Access denied", lvl=verbose)
        return False

    @staticmethod
    def _check_create_permission(subject, schema):
        for role in subject.account.roles:
            if role in schemastore[schema]["schema"]["roles_create"]:
                return True
        return False

    def _cancel_by_permission(self, schema, data, event):
        self.log("No permission:", schema, data, event.user.uuid, lvl=warn)

        msg = {
            "component": "isomer.events.objectmanager",
            "action": "fail",
            "data": {"reason": "No permission", "req": data.get("req")},
        }
        self.fire(send(event.client.uuid, msg))

    def _cancel_by_error(self, event, reason="malformed"):
        self.log("Bad request:", reason, lvl=warn)

        msg = {
            "component": "isomer.events.objectmanager",
            "action": "fail",
            "data": {"reason": reason, "req": event.data.get("req", None)},
        }
        self.fire(send(event.client.uuid, msg))

    def _get_schema(self, event):
        data = event.data

        if "schema" not in data:
            self._cancel_by_error(event, "no_schema")
            raise AttributeError
        if data["schema"] not in objectmodels.keys():
            self._cancel_by_error(event, "invalid_schema:" + data["schema"])
            raise AttributeError

        return data["schema"]

    @staticmethod
    def _get_filter(event):
        data = event.data
        if "filter" in data:
            object_filter = data["filter"]
        else:
            object_filter = {}

        return object_filter

    def _get_args(self, event):
        schema = self._get_schema(event)
        try:
            data = event.data
            user = event.user
            client = event.client
        except (KeyError, AttributeError) as e:
            self.log(
                "Error during argument extraction:", e, type(e), exc=True, lvl=error
            )
            self._cancel_by_error(event, "Invalid arguments")
            raise AttributeError

        return data, schema, user, client

    def _respond(self, notification, result, event):
        if notification:
            try:
                self.log("Firing notification", lvl=verbose)
                self.fireEvent(notification)
            except Exception as e:
                self.log("Transmission error during notification: %s" % e, lvl=error)

        if result:
            try:
                self.log("Transmitting result", lvl=verbose)
                if isinstance(event.data, dict):
                    result["data"]["req"] = event.data.get("req", None)
                self.fireEvent(send(event.client.uuid, result))
            except Exception as e:
                self.log(
                    "Transmission error during response: %s" % e, lvl=error, exc=True
                )
