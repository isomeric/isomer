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


Module clientmanager.floodprotection
====================================

Protection against erroneously flooding clients.


"""


__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from circuits import Timer, Event

from isomer.component import handler
from isomer.events.client import send

from isomer.ui.clientmanager.cli import CliManager


class reset_flood_counters(Event):
    pass


class reset_flood_offenders(Event):
    pass


class FloodProtectedManager(CliManager):
    """Deal with eventual client-side flooding"""

    def __init__(self, *args, **kwargs):
        super(FloodProtectedManager, self).__init__(*args, **kwargs)

        self._flooding = {}
        self._flood_counter = {}

        self._flood_counters_resetter = Timer(
            2, Event.create("reset_flood_counters"), persist=True
        ).register(self)
        self._flood_offender_resetter = Timer(
            10, Event.create("reset_flood_offenders"), persist=True
        ).register(self)

    @handler("reset_flood_counters")
    def _reset_flood_counters(self, *args):
        """Resets the flood counters on event trigger"""

        # self.log('Resetting flood counter')
        self._flood_counter = {}

    @handler("reset_flood_offenders")
    def _reset_flood_offenders(self, *args):
        """Resets the list of flood offenders on event trigger"""

        offenders = []
        # self.log('Resetting flood offenders')

        for offender, offence_time in self._flooding.items():
            if time() - offence_time < 10:
                self.log("Removed offender from flood list:", offender)
                offenders.append(offender)

        for offender in offenders:
            del self._flooding[offender]

    def _check_flood_protection(self, component, action, clientuuid):
        """Checks if any clients have been flooding the node"""

        if clientuuid not in self._flood_counter:
            self._flood_counter[clientuuid] = 0

        self._flood_counter[clientuuid] += 1

        if self._flood_counter[clientuuid] > 100:
            packet = {
                "component": "isomer.ui.clientmanager",
                "action": "Flooding",
                "data": True,
            }
            self.fireEvent(send(clientuuid, packet))
            self.log("Flooding from", clientuuid)
            return True
