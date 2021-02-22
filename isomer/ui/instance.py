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

Module: Instance.component
=======================

Instance management component.

"""


import requests
from simplejson.errors import JSONDecodeError
from urllib.parse import urljoin

from isomer.events.system import system_stop
from isomer.logger import error, critical, debug
from isomer.database import objectmodels
from isomer.events.system import authorized_event, isomer_event
from isomer.component import ConfigurableComponent, handler
from isomer.ui.store import DEFAULT_STORE_URL


class get_instance_data(authorized_event):
    """Request general information on the running instance"""
    roles = ['admin']


class upgrade_isomer(authorized_event):
    """Request an upgrade of Isomer for this instance"""
    roles = ['admin']


class restart_instance(authorized_event):
    """Request a restart of Isomer for this instance"""
    roles = ['admin']


class notify_restart_required(isomer_event):
    """Internal notification that a restart will be required """
    reason = ""


class InstanceInfo(ConfigurableComponent):
    """Instance overview information component for Isomer"""

    configprops = {
        'update_server': {'type': 'string', 'default': DEFAULT_STORE_URL},
        'auth': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {
                    'type': 'string',
                    'x-schema-form': {'type': 'password'}
                }
            },
            'default': {'username': '', 'password': ''}
        }
    }

    def __init__(self, *args, **kwargs):
        super(InstanceInfo, self).__init__('INSTANCEINFO', *args, **kwargs)

        # self.log(self.context.__dict__, pretty=True)

        systemconfig = objectmodels['systemconfig'].find_one({'active': True})

        self.needs_restart = False
        self.restart_reasons = []

        url = urljoin(self.config.update_server, "/store/isomer_enrol/")
        try:
            data = requests.get(
                url, auth=(
                    self.config.auth['username'], self.config.auth['password'])
            )
            self.latest_version = data.json()['isomer_enrol']
        except (requests.RequestException, JSONDecodeError, KeyError):
            self.log("Can't access store isomer version.", lvl=error)
            self.log("Store access error:\n", exc=True, lvl=debug)
            self.latest_version = "N/A"

        self.current_version = "N/A"

        for item in systemconfig.packages:
            if item['name'] == "isomer":
                self.current_version = ".".join(item['version'].split(".")[:3])
                continue

    @handler(get_instance_data)
    def get_instance_data(self, event):
        """Handler for general information on the running instance"""

        obj = self.context.obj

        result = {
            'needs_restart': self.needs_restart,
            'restart_reasons': self.restart_reasons,
            'latest_version': self.latest_version,
            'current_version': self.current_version,
            'context': {
                'acting_environment': obj['acting_environment'],
                'config': obj['config'],
                'dbhost': obj['dbhost'],
                'dbname': obj['dbname'],
                'environment': obj['environment'],
                'instance': obj['instance'],
                'instance_configuration': obj['instance_configuration']
            }
        }

        self._respond(event, result)
        return

    @handler("notify_restart_required")
    def notify_restart_required(self, reason):
        """Toggles the user interface notification to restart the instance"""

        self.log("Restart requested by another component for:", reason)
        self.needs_restart = True
        if reason not in self.restart_reasons:
            self.restart_reasons.append(reason)

    @handler(upgrade_isomer)
    def upgrade_isomer(self, event):
        """Upgrade Isomer"""

        self.log("Beginning Isomer upgrade.")

        upgraded_version = self.latest_version

        reason = "Upgraded Isomer to " + upgraded_version

        self.fireEvent(
            notify_restart_required(reason)
        )

        self._respond(event, reason)

    @handler(restart_instance)
    def restart_instance(self):
        """Terminate the currently running instance and restart it"""

        self.log("Terminating to restart on admin request", lvl=critical)

        open("/tmp/isomer_toggle_%s" % self.context.obj['instance'], "a").close()

        self.fireEvent(system_stop())
