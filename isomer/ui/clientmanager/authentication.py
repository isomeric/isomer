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


Module clientmanager.authentication
===================================

Handles authentication and authorization related aspects


"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import json

from circuits.net.events import write

from isomer.component import handler

from isomer.events.client import clientdisconnect, send, authenticationrequest, \
    userlogin
from isomer.events.system import get_user_events, get_anonymous_events
from isomer.logger import debug, critical, verbose, error, warn, network, info
from isomer.misc import i18n as _

from isomer.ui.clientobjects import Client, User

from isomer.ui.clientmanager.basemanager import ClientBaseManager


class AuthenticationManager(ClientBaseManager):
    """Handles authentication and authorization related aspects"""

    def __init__(self, *args, **kwargs):
        super(AuthenticationManager, self).__init__(*args, **kwargs)

        self.authorized_events = {}
        self.anonymous_events = {}

    @handler("ready")
    def ready(self):
        """Compile events"""

        self.authorized_events = get_user_events()
        self.anonymous_events = get_anonymous_events()

    @handler("authentication", channel="auth")
    def authentication(self, event):
        """Links the client to the granted account and profile,
        then notifies the client"""

        try:
            self.log(
                "Authorization has been granted by DB check:", event.username, lvl=debug
            )

            account, profile, clientconfig = event.userdata

            useruuid = event.useruuid
            originatingclientuuid = event.clientuuid
            clientuuid = clientconfig.uuid

            if clientuuid != originatingclientuuid:
                self.log("Mutating client uuid to request id:", clientuuid, lvl=network)
            # Assign client to user
            if useruuid in self._users:
                signedinuser = self._users[useruuid]
            else:
                signedinuser = User(account, profile, useruuid)
                self._users[account.uuid] = signedinuser

            if clientuuid in signedinuser.clients:
                self.log("Client configuration already logged in.", lvl=critical)
                # TODO: What now??
                # Probably senseful would be to add the socket to the
                # client's other socket
                # The clients would be identical then - that could cause
                # problems
                # which could be remedied by duplicating the configuration
            else:
                signedinuser.clients.append(clientuuid)
                self.log(
                    "Active client (",
                    clientuuid,
                    ") registered to " "user",
                    useruuid,
                    lvl=debug,
                )

            # Update socket..
            socket = self._sockets[event.sock]
            socket.clientuuid = clientuuid
            self._sockets[event.sock] = socket

            # ..and client lists

            try:
                language = clientconfig.language
            except AttributeError:
                language = "en"

            # TODO: Rewrite and simplify this:
            newclient = Client(
                sock=event.sock,
                ip=socket.ip,
                clientuuid=clientuuid,
                useruuid=useruuid,
                name=clientconfig.name,
                config=clientconfig,
                language=language,
            )

            del self._clients[originatingclientuuid]
            self._clients[clientuuid] = newclient

            authpacket = {
                "component": "auth",
                "action": "login",
                "data": account.serializablefields(),
            }
            self.log("Transmitting Authorization to client", authpacket, lvl=network)
            self.fireEvent(write(event.sock, json.dumps(authpacket)), "wsserver")

            profilepacket = {
                "component": "profile",
                "action": "get",
                "data": profile.serializablefields(),
            }
            self.log("Transmitting Profile to client", profilepacket, lvl=network)
            self.fireEvent(write(event.sock, json.dumps(profilepacket)), "wsserver")

            clientconfigpacket = {
                "component": "clientconfig",
                "action": "get",
                "data": clientconfig.serializablefields(),
            }
            self.log(
                "Transmitting client configuration to client",
                clientconfigpacket,
                lvl=network,
            )
            self.fireEvent(
                write(event.sock, json.dumps(clientconfigpacket)), "wsserver"
            )

            self.fireEvent(userlogin(clientuuid, useruuid, clientconfig, signedinuser))

            self.log(
                "User configured: Name",
                signedinuser.account.name,
                "Profile",
                signedinuser.profile.uuid,
                "Clients",
                signedinuser.clients,
                lvl=debug,
            )

        except Exception as e:
            self.log(
                "Error (%s, %s) during auth grant: %s" % (type(e), e, event), lvl=error
            )

    def _handle_authentication_events(self, data, action, clientuuid, sock):
        """Handler for authentication events"""

        # TODO: Move this stuff over to ./auth.py
        if action in ("login", "autologin"):
            try:
                self.log("Login request", lvl=verbose)

                if action == "autologin":
                    username = password = None
                    requested_clientuuid = data
                    auto = True

                    self.log("Autologin for", requested_clientuuid, lvl=debug)
                else:
                    username = data["username"]
                    password = data["password"]

                    if "clientuuid" in data:
                        requested_clientuuid = data["clientuuid"]
                    else:
                        requested_clientuuid = None
                    auto = False

                    self.log("Auth request by", username, lvl=verbose)

                self.fireEvent(
                    authenticationrequest(
                        username, password, clientuuid, requested_clientuuid, sock, auto
                    ),
                    "auth",
                )
                return
            except Exception as e:
                self.log("Login failed: ", e, type(e), lvl=warn, exc=True)
        elif action == "logout":
            self.log("User logged out, refreshing client.", lvl=network)
            try:
                if clientuuid in self._clients:
                    client = self._clients[clientuuid]
                    user_id = client.useruuid
                    if client.useruuid:
                        self.log("Logout client uuid: ", clientuuid)
                        self._logout_client(client.useruuid, clientuuid)
                    self.fireEvent(clientdisconnect(clientuuid))
                else:
                    self.log("Client is not connected!", lvl=warn)
            except Exception as e:
                self.log(
                    "Error during client logout: ", e, type(e), lvl=error, exc=True
                )
        else:
            self.log("Unsupported auth action requested:", action, lvl=warn)

    def _handle_authorized_events(self, component, action, data, user, client):
        """Isolated communication link for authorized events."""

        try:
            if component == "debugger":
                self.log(component, action, data, user, client, lvl=info)

            if not user and component in self.authorized_events.keys():
                self.log(
                    "Unknown client tried to do an authenticated " "operation: %s",
                    component,
                    action,
                    data,
                    user,
                )
                return

            event = self.authorized_events[component][action]["event"](
                user, action, data, client
            )

            self.log("Authorized event roles:", event.roles, lvl=verbose)
            if not self._check_permissions(user, event):
                result = {
                    "component": "isomer.ui.clientmanager",
                    "action": "Permission",
                    "data": _("You have no role that allows this action.", lang="de"),
                }
                self.fireEvent(send(event.client.uuid, result))
                return

            self.log(
                "Firing authorized event: ",
                component,
                action,
                str(data)[:100],
                lvl=debug,
            )
            # self.log("", (user, action, data, client), lvl=critical)
            self.fireEvent(event)
        except Exception as e:
            self.log(
                "Critical error during authorized event handling:",
                component,
                action,
                e,
                type(e),
                lvl=critical,
                exc=True,
            )

    def _handle_anonymous_events(self, component, action, data, client):
        """Handler for anonymous (public) events"""
        try:
            event = self.anonymous_events[component][action]["event"]

            self.log(
                "Firing anonymous event: ",
                component,
                action,
                str(data)[:20],
                lvl=network,
            )
            # self.log("", (user, action, data, client), lvl=critical)
            self.fireEvent(event(action, data, client))
        except Exception as e:
            self.log(
                "Critical error during anonymous event handling:",
                component,
                action,
                e,
                type(e),
                lvl=critical,
                exc=True,
            )

    def _check_permissions(self, user, event):
        """Checks if the user has in any role that allows to fire the event."""

        for role in user.account.roles:
            if role in event.roles:
                self.log("Access granted", lvl=verbose)
                return True

        self.log("Access denied", lvl=verbose)
        return False
