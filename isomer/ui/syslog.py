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

"""Live system logging (WiP!)"""

from circuits import Event, Timer

from isomer.component import ConfigurableComponent, handler
from isomer.events.client import send  # , clientdisconnect
from isomer.events.system import authorized_event
from isomer.logger import error, debug, get_logfile


class history(authorized_event):
    pass


class subscribe(authorized_event):
    pass


class Syslog(ConfigurableComponent):
    """
    System log access component

    Handles all the frontend log history requests.

    """

    def __init__(self, *args):
        super(Syslog, self).__init__("SYSLOG", *args)

        self.log("Started")

        self.subscribers = []

        self.log_file = open(get_logfile())
        self.log_position = 0

        self.follow_timer = Timer(1, Event.create("syslog_follow"), persist=True)

    @handler(subscribe)
    def subscribe(self, event):
        self.subscribers.append(event.client.uuid)

    @handler("clientdisconnect", priority=1000)
    def disconnect(self, event):
        self.log("Disconnected: ", event.clientuuid, lvl=debug)
        if event.clientuuid in self.subscribers:
            self.subscribers.remove(event.clientuuid)

    def _logupdate(self, new_messages):
        packet = {
            "component": "isomer.ui.syslog",
            "action": "update",
            "data": new_messages,
        }

        for subscriber in self.subscribers:
            self.fireEvent(send(subscriber, packet, fail_quiet=True))

    @handler("syslog_follow")
    def follow(self):
        where = self.log_file.tell()
        line = self.log_file.readline()
        if not line:
            self.log_file.seek(where)
        else:
            self._logupdate(line)

    @handler(history)
    def history(self, event):
        try:
            limit = event.data["limit"]
            end = event.data["end"]
        except (KeyError, AttributeError) as e:
            self.log("Error during event lookup:", e, type(e), exc=True, lvl=error)
            return

        self.log("History requested:", limit, end, lvl=debug)

        messages = []

        history_packet = {
            "component": "isomer.ui.syslog",
            "action": "history",
            "data": {"limit": limit, "end": end, "history": messages},
        }
        self.fireEvent(send(event.client.uuid, history_packet))
