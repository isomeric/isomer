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


Module clientmanager.languages
==============================

Language support for clients

"""

from isomer.component import handler

from isomer.events.system import anonymous_event
from isomer.events.client import send

from isomer.misc import i18n as _, all_languages, language_token_to_name
from isomer.logger import verbose, warn

from isomer.ui.clientmanager.floodprotection import FloodProtectedManager


class selectlanguage(anonymous_event):
    pass


class getlanguages(anonymous_event):
    pass


class LanguageManager(FloodProtectedManager):
    """Adds language support for clients"""

    @handler(selectlanguage)
    def selectlanguage(self, event):
        """Store client's selection of a new translation"""

        self.log("Language selection event:", event.client, pretty=True)

        if event.data not in all_languages():
            self.log("Unavailable language selected:", event.data, lvl=warn)
            language = None
        else:
            language = event.data

        if language is None:
            language = "en"

        event.client.language = language

        if event.client.config is not None:
            event.client.config.language = language
            event.client.config.save()

    @handler(getlanguages)
    def getlanguages(self, event):
        """Compile and return a human readable list of registered translations"""

        self.log("Client requests all languages.", lvl=verbose)
        result = {
            "component": "isomer.ui.clientmanager",
            "action": "getlanguages",
            "data": language_token_to_name(all_languages()),
        }
        self.fireEvent(send(event.client.uuid, result))
