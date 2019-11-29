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


Module clientmanager.latency
============================

Latency analysis for clients

"""

from time import time

from isomer.events.system import authorized_event
from isomer.component import handler
from isomer.events.client import send
from isomer.logger import verbose

from isomer.ui.clientmanager.languages import LanguageManager


class ping(authorized_event):
    pass


class LatencyManager(LanguageManager):
    """Respond to authorized ping requests"""

    @handler(ping)
    def ping(self, event):
        """Perform a ping to measure client <-> node latency"""

        self.log("Client ping received:", event.data, lvl=verbose)
        response = {
            "component": "isomer.ui.clientmanager",
            "action": "pong",
            "data": [event.data, time() * 1000],
        }

        self.fire(send(event.client.uuid, response))
