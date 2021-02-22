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

Module: objectmanager.subscriptions
===================================

Subscription management for objects


"""

from isomer.component import handler
from isomer.events.client import send
from isomer.events.objectmanager import subscribe, unsubscribe
from isomer.logger import verbose
from isomer.ui.objectmanager.roles import RoleOperations


class SubscriptionOperations(RoleOperations):
    """Adds subscription functionality"""

    @handler(subscribe)
    def subscribe(self, event):
        """Subscribe to an object's future changes"""
        uuids = event.data

        if not isinstance(uuids, list):
            uuids = [uuids]

        subscribed = []
        for uuid in uuids:
            try:
                self._add_subscription(uuid, event)
                subscribed.append(uuid)
            except KeyError:
                continue

        result = {
            "component": "isomer.events.objectmanager",
            "action": "subscribe",
            "data": {"uuid": subscribed, "success": True},
        }
        self._respond(None, result, event)

    def _add_subscription(self, uuid, event):
        self.log("Adding subscription for", uuid, event.user, lvl=verbose)
        if uuid in self.subscriptions:
            if event.client.uuid not in self.subscriptions[uuid]:
                self.subscriptions[uuid][event.client.uuid] = event.user
        else:
            self.subscriptions[uuid] = {event.client.uuid: event.user}

    @handler(unsubscribe)
    def unsubscribe(self, event):
        """Unsubscribe from an object's future changes"""
        # TODO: Automatic Unsubscription
        uuids = event.data

        if not isinstance(uuids, list):
            uuids = [uuids]

        result = []

        for uuid in uuids:
            if uuid in self.subscriptions:
                self.subscriptions[uuid].pop(event.client.uuid)

                if len(self.subscriptions[uuid]) == 0:
                    del self.subscriptions[uuid]

                result.append(uuid)

        result = {
            "component": "isomer.events.objectmanager",
            "action": "unsubscribe",
            "data": {"uuid": result, "success": True},
        }

        self._respond(None, result, event)

    @handler("updatesubscriptions")
    def update_subscriptions(self, event):
        """OM event handler for to be stored and client shared objectmodels
        :param event: OMRequest with uuid, schema and object data
        """

        # self.log("Event: '%s'" % event.__dict__)
        try:
            self._update_subscribers(event.schema, event.data)

        except Exception as e:
            self.log("Error during subscription update: ", type(e), e, exc=True)

    def _update_subscribers(self, update_schema, update_object):
        # Notify frontend subscribers

        self.log("Notifying subscribers about update.", lvl=verbose)
        if update_object.uuid in self.subscriptions:
            update = {
                "component": "isomer.events.objectmanager",
                "action": "update",
                "data": {
                    "schema": update_schema,
                    "uuid": update_object.uuid,
                    "object": update_object.serializablefields(),
                },
            }

            # pprint(self.subscriptions)

            for client, recipient in self.subscriptions[update_object.uuid].items():
                if not self._check_permissions(update_schema, recipient, "read", update_object):
                    continue

                self.log("Notifying subscriber: ", client, recipient, lvl=verbose)
                self.fireEvent(send(client, update))
