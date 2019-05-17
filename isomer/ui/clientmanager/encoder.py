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


Module clientmanager.encoder
============================

Enhanced JSON encoding


"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import datetime
import json


class ComplexEncoder(json.JSONEncoder):
    """A JSON encoder that converts dates to ISO 8601 formatting"""

    def default(self, obj):
        """Convert datetime objects to ISO 8601 format"""
        if isinstance(obj, (datetime.time, datetime.date)):
            return obj.isoformat()
            # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
