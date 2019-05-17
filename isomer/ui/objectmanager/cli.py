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

Module: objectmanager.cli
=========================

Command line interface functionality for debugging object handling


"""
from circuits import Event

from isomer.debugger import cli_register_event
from isomer.component import handler

from isomer.ui.objectmanager.basemanager import ObjectBaseManager


class cli_subscriptions(Event):
    """Display a list of all registered subscriptions"""

    pass


class CliManager(ObjectBaseManager):
    """Adds cli commands to inspect object management"""

    def __init__(self, *args, **kwargs):
        super(CliManager, self).__init__(*args, **kwargs)

        self.fireEvent(cli_register_event("om_subscriptions", cli_subscriptions))

    @handler("cli_subscriptions")
    def cli_subscriptions(self, event):
        self.log("Subscriptions", self.subscriptions, pretty=True)
