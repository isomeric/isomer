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

Module: Configurator
=====================


"""

from isomer.events.client import send
from isomer.events.system import reload_configuration
from isomer.component import ConfigurableComponent, authorized_event, handler
from isomer.schemata.component import ComponentConfigSchemaTemplate as Schema
from isomer.schemata.base import uuid_object
from isomer.database import ValidationError
from isomer.logger import error, warn
from formal import model_factory


class getlist(authorized_event):
    """A client requires a schema to validate data or display a form"""

    roles = ["admin"]


class get(authorized_event):
    """A client requires a schema to validate data or display a form"""

    roles = ["admin"]
    tags = [
        {"name": "admin", "description": "Administrative topics"},
        {"name": "configuration", "description": "Configuration topics"}
    ]
    summary = "Get component configuration data"
    channel_hints = {
        'uuid': {
        }
    }

    args = {
        "uuid": uuid_object()
    }


class put(authorized_event):
    """A client requires a schema to validate data or display a form"""

    roles = ["admin"]
    tags = [
        {"name": "admin", "description": "Administrative topics"},
        {"name": "configuration", "description": "Configuration topics"}
    ]
    summary = "Store component configuration data"
    channel_hints = {
        'configuration': {}
    }

    args = {
        'configuration': {'type': 'object'}
    }


class Configurator(ConfigurableComponent):
    """
    Provides a common configuration interface for all Isomer components.

    (You're probably looking at it right now)
    """

    channel = "isomer-web"

    configprops = {}

    def __init__(self, *args):
        super(Configurator, self).__init__("CONF", *args)

    @handler(getlist)
    def getlist(self, event):
        """Processes configuration list requests

        :param event:
        """

        try:

            componentlist = model_factory(Schema).find({})
            data = []
            for comp in componentlist:
                try:
                    data.append(
                        {
                            "name": comp.name,
                            "uuid": comp.uuid,
                            "class": comp.componentclass,
                            "active": comp.active,
                            "present": comp.name in self.names
                        }
                    )
                except AttributeError:
                    self.log(
                        "Bad component without component class encountered:", lvl=warn
                    )
                    self.log(comp.serializablefields(), pretty=True, lvl=warn)

            data = sorted(data, key=lambda x: x["name"])

            response = {
                "component": "isomer.ui.configurator",
                "action": "getlist",
                "data": data,
            }
            self.fireEvent(send(event.client.uuid, response))
            return
        except Exception as e:
            self.log("List error: ", e, type(e), lvl=error, exc=True)

    @handler(put)
    def put(self, event):
        """Store a given configuration"""

        self.log("Configuration put request ", event.user)

        try:
            component = model_factory(Schema).find_one({"uuid": event.data["uuid"]})

            component.update(event.data)
            component.save()

            response = {
                "component": "isomer.ui.configurator",
                "action": "put",
                "data": True,
            }
            self.log("Updated component configuration:", component.name)

            self.fireEvent(reload_configuration(component.name))
        except (KeyError, ValueError, ValidationError, PermissionError) as e:
            response = {
                "component": "isomer.ui.configurator",
                "action": "put",
                "data": False,
            }
            self.log(
                "Storing component configuration failed: ",
                type(e),
                e,
                exc=True,
                lvl=error,
            )

        self.fireEvent(send(event.client.uuid, response))
        return

    @handler(get)
    def get(self, event):
        """Get a stored configuration"""

        try:
            comp = event.data["uuid"]
        except KeyError:
            comp = None

        if not comp:
            self.log("Invalid get request without schema or component", lvl=error)
            return

        self.log("Config data get  request for ", event.data, "from", event.user)

        component = model_factory(Schema).find_one({"uuid": comp})
        response = {
            "component": "isomer.ui.configurator",
            "action": "get",
            "data": component.serializablefields(),
        }
        self.fireEvent(send(event.client.uuid, response))
