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

Module: store.component
=======================

Store management component.

"""
from isomer.misc.path import get_path
from isomer.tool import get_next_environment
from isomer.events.client import send
from isomer.ui.store import DEFAULT_STORE_URL
from isomer.ui.store.inventory import get_store, get_inventory
from isomer.ui.store import get_store_inventory, install, remove, update, update_all
from isomer.component import ConfigurableComponent, handler
from isomer.ui.instance import notify_restart_required


class Store(ConfigurableComponent):
    """Software store for Isomer"""

    configprops = {
        'store_url': {
            'type': 'string',
            'title': 'Store URL',
            'description': 'Specify alternate store url (Default:%s)'
                           % DEFAULT_STORE_URL,
            'default': DEFAULT_STORE_URL
        }
    }

    def __init__(self, *args, **kwargs):
        super(Store, self).__init__('STORE', *args, **kwargs)

    @handler(get_store_inventory)
    def get_store_inventory(self, event):
        """Fetch store inventory and transmit back to client."""

        store_inventory = get_store(self.config.store_url)
        local_inventory = get_inventory(self.context)

        response = {
            'component': 'isomer.ui.store',
            'action': 'get_store_inventory',
            'data': {
                'store': store_inventory,
                'local': local_inventory
            }
        }

        self.fireEvent(send(event.client.uuid, response))

    @handler(install)
    def install(self, event):
        """Installs a new Isomer package on the running instance"""
        self.log("Installing package:", event.data)

        instance_config = self.context.obj["instance_configuration"]
        # repository = get_path("lib", "repository")

        environments = instance_config["environments"]

        active = instance_config["environment"]

        next_environment = get_next_environment(self.context)

        self.fireEvent(notify_restart_required(reason="Module installed: " + event.data))
