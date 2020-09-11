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


Module clientmanager.cli
========================

Command line interface functionality for debugging client handling

"""

from collections import namedtuple

from circuits import Event

from isomer.component import handler
from isomer.debugger import cli_register_event
from isomer.misc import i18n as _
from isomer.misc.std import std_table

from isomer.ui.clientmanager.authentication import AuthenticationManager


class cli_users(Event):
    """Display the list of connected users from the clientmanager"""

    pass


class cli_clients(Event):
    """Display the list of connected clients from the clientmanager"""

    pass


class cli_client(Event):
    """Display detailed info about a connected client"""

    pass


class cli_events(Event):
    """Display the list of authorized and anonymous events"""

    pass


class cli_sources(Event):
    """Display the list of authorized and anonymous events"""

    pass


class cli_who(Event):
    """Display the list of all users and clients"""

    pass


class CliManager(AuthenticationManager):
    """Command Line Interface support"""

    def __init__(self, *args, **kwargs):
        super(CliManager, self).__init__(*args, **kwargs)

        self.fireEvent(cli_register_event("users", cli_users))
        self.fireEvent(cli_register_event("clients", cli_clients))
        self.fireEvent(cli_register_event("client", cli_client))
        self.fireEvent(cli_register_event("events", cli_events))
        self.fireEvent(cli_register_event("sources", cli_sources))
        self.fireEvent(cli_register_event("who", cli_who))

    @handler("cli_client")
    def client_details(self, *args):
        """Display known details about a given client"""

        self.log(_("Client details:", lang="de"))
        client = self._clients[args[0]]

        self.log(
            "UUID:",
            client.uuid,
            "IP:",
            client.ip,
            "Name:",
            client.name,
            "User:",
            self._users[client.useruuid],
            pretty=True,
        )

    @handler("cli_clients")
    def client_list(self, *args):
        """Display a list of connected clients"""
        if len(self._clients) == 0:
            self.log("No clients connected")
        else:
            self.log(self._clients, pretty=True)

    @handler("cli_users")
    def users_list(self, *args):
        """Display a list of connected users"""
        if len(self._users) == 0:
            self.log("No users connected")
        else:
            self.log(self._users, pretty=True)

    @handler("cli_sources")
    def sources_list(self, *args):
        """Display a list of all registered events"""

        sources = {}
        sources.update(self.authorized_events)
        sources.update(self.anonymous_events)

        for source in sources:
            self.log(source, pretty=True)

    @handler("cli_events")
    def events_list(self, *args):
        """Display a list of all registered events"""

        def merge(a, b, path=None):
            """Merges b into a"""

            if path is None:
                path = []
            for key in b:
                if key in a:
                    if isinstance(a[key], dict) and isinstance(b[key], dict):
                        merge(a[key], b[key], path + [str(key)])
                    elif a[key] == b[key]:
                        pass  # same leaf value
                    else:
                        raise Exception("Conflict at %s" % ".".join(path + [str(key)]))
                else:
                    a[key] = b[key]
            return a

        events = {}
        sources = merge(self.authorized_events, self.anonymous_events)

        for source, source_events in sources.items():
            events[source] = []
            for item in source_events:
                events[source].append(item)

        self.log(events, pretty=True)

    @handler("cli_who")
    def who(self, *args):
        """Display a table of connected users and clients"""
        if len(self._users) == 0:
            self.log("No users connected")
            if len(self._clients) == 0:
                self.log("No clients connected")
                return

        Row = namedtuple("Row", ["User", "Client", "IP"])
        rows = []

        for user in self._users.values():
            for key, client in self._clients.items():
                if client.useruuid == user.uuid:
                    row = Row(user.account.name, key, client.ip)
                    rows.append(row)

        for key, client in self._clients.items():
            if client.useruuid is None:
                row = Row("ANON", key, client.ip)
                rows.append(row)

        self.log("\n" + std_table(rows))
