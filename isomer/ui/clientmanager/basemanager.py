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


Module clientmanager.basemanager
================================

Basic client management functionality and component set up.


"""

import json
from base64 import b64decode
from time import time
from uuid import uuid4

from circuits.net.events import write
from isomer.component import ConfigurableComponent, handler
from isomer.database import objectmodels
from isomer.events.client import clientdisconnect, userlogout, send

from isomer.logger import debug, critical, verbose, error, warn, network, info
from isomer.misc import i18n as _
from isomer.ui.clientobjects import Socket, Client, User

from isomer.ui.clientmanager.encoder import ComplexEncoder


class ClientBaseManager(ConfigurableComponent):
    """
    Handles client connections and requests as well as client-outbound
    communication.
    """

    channel = "isomer-web"

    def __init__(self, *args, **kwargs):
        super(ClientBaseManager, self).__init__("CM", *args, **kwargs)

        self._clients = {}
        self._sockets = {}
        self._users = {}
        self._count = 0
        self._user_mapping = {}

    @handler("disconnect", channel="wsserver")
    def disconnect(self, sock):
        """Handles socket disconnections"""

        self.log("Disconnect ", sock, lvl=debug)

        try:
            if sock in self._sockets:
                self.log("Getting socket", lvl=debug)
                socket_object = self._sockets[sock]
                self.log("Getting clientuuid", lvl=debug)
                clientuuid = socket_object.clientuuid
                self.log("getting useruuid", lvl=debug)
                useruuid = self._clients[clientuuid].useruuid

                self.log("Firing disconnect event", lvl=debug)
                self.fireEvent(
                    clientdisconnect(clientuuid, self._clients[clientuuid].useruuid)
                )

                self.log("Logging out relevant client", lvl=debug)
                if useruuid is not None:
                    self.log("Client was logged in", lvl=debug)
                    try:
                        self._logout_client(useruuid, clientuuid)
                        self.log("Client logged out", useruuid, clientuuid)
                    except Exception as e:
                        self.log(
                            "Couldn't clean up logged in user! ",
                            self._users[useruuid],
                            e,
                            type(e),
                            lvl=critical,
                        )
                self.log("Deleting Client (", self._clients.keys, ")", lvl=debug)
                del self._clients[clientuuid]
                self.log("Deleting Socket", lvl=debug)
                del self._sockets[sock]
        except Exception as e:
            self.log("Error during disconnect handling: ", e, type(e), lvl=critical)

    def _logout_client(self, useruuid, clientuuid):
        """Log out a client and possibly associated user"""

        self.log("Cleaning up client of logged in user.", lvl=debug)
        try:
            self._users[useruuid].clients.remove(clientuuid)
            if len(self._users[useruuid].clients) == 0:
                self.log("Last client of user disconnected.", lvl=verbose)

                self.fireEvent(userlogout(useruuid, clientuuid))
                del self._users[useruuid]

            self._clients[clientuuid].useruuid = None
        except Exception as e:
            self.log(
                "Error during client logout: ",
                e,
                type(e),
                clientuuid,
                useruuid,
                lvl=error,
                exc=True,
            )

    @handler("connect", channel="wsserver")
    def connect(self, *args):
        """Registers new sockets and their clients and allocates uuids"""

        self.log("Connect ", args, lvl=verbose)

        try:
            sock = args[0]
            ip = args[1]

            if sock not in self._sockets:
                self.log("New client connected:", ip, lvl=debug)
                clientuuid = str(uuid4())
                self._sockets[sock] = Socket(ip, clientuuid)
                # Key uuid is temporary, until signin, will then be replaced
                #  with account uuid

                self._clients[clientuuid] = Client(
                    sock=sock, ip=ip, clientuuid=clientuuid
                )

                self.log("Client connected:", clientuuid, lvl=debug)
            else:
                self.log("Old IP reconnected!", lvl=warn)
                #     self.fireEvent(write(sock, "Another client is
                # connecting from your IP!"))
                #     self._sockets[sock] = (ip, uuid.uuid4())
        except Exception as e:
            self.log("Error during connect: ", e, type(e), lvl=critical)

    def send(self, event):
        """Sends a packet to an already known user or one of his clients by
        UUID"""

        try:
            jsonpacket = json.dumps(event.packet, cls=ComplexEncoder)
            if event.sendtype == "user":
                # TODO: I think, caching a user name <-> uuid table would
                # make sense instead of looking this up all the time.

                if event.uuid is None:
                    userobject = objectmodels["user"].find_one({"name": event.username})
                else:
                    userobject = objectmodels["user"].find_one({"uuid": event.uuid})

                if userobject is None:
                    self.log("No user by that name known.", lvl=warn)
                    return
                else:
                    uuid = userobject.uuid

                self.log(
                    "Broadcasting to all of users clients: '%s': '%s"
                    % (uuid, str(event.packet)[:20]),
                    lvl=network,
                )
                if uuid not in self._users:
                    self.log("User not connected!", event, lvl=critical)
                    return
                clients = self._users[uuid].clients

                for clientuuid in clients:
                    sock = self._clients[clientuuid].sock

                    if not event.raw:
                        self.log("Sending json to client", jsonpacket[:50], lvl=network)

                        self.fireEvent(write(sock, jsonpacket), "wsserver")
                    else:
                        self.log("Sending raw data to client")
                        self.fireEvent(write(sock, event.packet), "wsserver")
            else:  # only to client
                self.log(
                    "Sending to user's client: '%s': '%s'"
                    % (event.uuid, jsonpacket[:20]),
                    lvl=network,
                )
                if event.uuid not in self._clients:
                    if not event.fail_quiet:
                        self.log("Unknown client!", event.uuid, lvl=critical)
                        self.log("Clients:", self._clients, lvl=debug)
                    return

                sock = self._clients[event.uuid].sock
                if not event.raw:
                    self.fireEvent(write(sock, jsonpacket), "wsserver")
                else:
                    self.log("Sending raw data to client", lvl=network)
                    self.fireEvent(write(sock, event.packet[:20]), "wsserver")

        except Exception as e:
            self.log(
                "Exception during sending: %s (%s)" % (e, type(e)),
                lvl=critical,
                exc=True,
            )

    def broadcast(self, event):
        """Broadcasts an event either to all users or clients or a given group,
        depending on event flag"""
        try:
            if event.broadcasttype == "users":
                if len(self._users) > 0:
                    self.log("Broadcasting to all users:", event.content, lvl=network)
                    for useruuid in self._users.keys():
                        self.fireEvent(send(useruuid, event.content, sendtype="user"))
                        # else:
                        #    self.log("Not broadcasting, no users connected.",
                        #            lvl=debug)

            elif event.broadcasttype == "clients":
                if len(self._clients) > 0:
                    self.log(
                        "Broadcasting to all clients: ", event.content, lvl=network
                    )
                    for client in self._clients.values():
                        self.fireEvent(write(client.sock, event.content), "wsserver")
                        # else:
                        #    self.log("Not broadcasting, no clients
                        # connected.",
                        #            lvl=debug)
            elif event.broadcasttype in ("usergroup", "clientgroup"):
                if len(event.group) > 0:
                    self.log(
                        "Broadcasting to group: ", event.content, event.group,
                        lvl=network
                    )
                    for participant in set(event.group):
                        if event.broadcasttype == 'usergroup':
                            broadcast_type = "user"
                        else:
                            broadcast_type = "client"

                        broadcast = send(participant, event.content,
                                         sendtype=broadcast_type)
                        self.fireEvent(broadcast)
            elif event.broadcasttype == "socks":
                if len(self._sockets) > 0:
                    self.log("Emergency?! Broadcasting to all sockets: ", event.content)
                    for sock in self._sockets:
                        self.fireEvent(write(sock, event.content), "wsserver")
                        # else:
                        #    self.log("Not broadcasting, no sockets
                        # connected.",
                        #            lvl=debug)

        except Exception as e:
            self.log("Error during broadcast: ", e, type(e), lvl=critical)

    @handler("read", channel="wsserver")
    def read(self, *args):
        """Handles raw client requests and distributes them to the
        appropriate components"""

        self.log("Beginning new transaction: ", args, lvl=network)

        sock = msg = user = password = client = client_uuid = \
            user_uuid = request_data = request_action = None

        try:
            sock, msg = args[0], args[1]
            # self.log("", msg)

            client_uuid = self._sockets[sock].clientuuid
        except Exception as e:
            self.log("Receiving error: ", e, type(e), lvl=error, exc=True)
            return

        if sock is None or msg is None:
            self.log("Socket or message are invalid!", lvl=error)
            return

        if client_uuid in self._flooding:
            return

        try:
            msg = json.loads(msg)
            self.log("Message from client received: ", msg, lvl=network)
        except Exception as e:
            self.log("JSON Decoding failed! %s (%s of %s)" % (msg, e, type(e)))
            return

        try:
            request_component = msg["component"]
            request_action = msg["action"]
        except (KeyError, AttributeError) as e:
            self.log("Unpacking error: ", msg, e, type(e), lvl=error)
            return

        if self._check_flood_protection(request_component, request_action, client_uuid):
            self.log("Flood protection triggered")
            self._flooding[client_uuid] = time()

        try:
            # TODO: Do not unpickle or decode anything from unsafe events
            request_data = msg["data"]
            if isinstance(request_data, (dict, list)) and "raw" in request_data:
                # self.log(request_data['raw'], lvl=critical)
                request_data["raw"] = b64decode(request_data["raw"])
                # self.log(request_data['raw'])
        except (KeyError, AttributeError) as e:
            self.log("No payload.", lvl=network)
            request_data = None

        if request_component == "auth":
            self._handle_authentication_events(
                request_data, request_action, client_uuid, sock
            )
            return
        else:
            self._forward_event(
                client_uuid, request_component, request_action, request_data
            )

    def _forward_event(
        self, client_uuid, request_component, request_action, request_data
    ):
        """Determine what exactly to do with the event and forward it to its
        destination"""
        try:
            client = self._clients[client_uuid]
        except KeyError as e:
            self.log("Could not get client for request!", e, type(e), lvl=warn)
            return

        if (
            request_component in self.anonymous_events
            and request_action in self.anonymous_events[request_component]
        ):
            self.log("Executing anonymous event:", request_component, request_action)
            try:
                self._handle_anonymous_events(
                    request_component, request_action, request_data, client
                )
            except Exception as e:
                self.log("Anonymous request failed:", e, type(e), lvl=warn, exc=True)
            return

        elif request_component in self.authorized_events:
            try:
                user_uuid = client.useruuid
                self.log(
                    "Authenticated operation requested by ",
                    user_uuid,
                    client.config,
                    lvl=network,
                )
            except Exception as e:
                self.log("No user_uuid!", e, type(e), lvl=critical)
                return

            self.log("Checking if user is logged in", lvl=verbose)

            try:
                user = self._users[user_uuid]
            except KeyError:
                if not (
                    request_action == "ping"
                    and request_component == "isomer.ui.clientmanager"
                ):
                    self.log("User not logged in.", lvl=warn)

                return

            self.log("Handling event:", request_component, request_action, lvl=verbose)
            try:
                self._handle_authorized_events(
                    request_component, request_action, request_data, user, client
                )
            except Exception as e:
                self.log("User request failed: ", e, type(e), lvl=warn, exc=True)
        else:
            self.log(
                "Invalid event received:", request_component, request_action, lvl=warn
            )
