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


Module: Events.Schemamanager
============================

Major Isomer event declarations


"""

from isomer.events.system import authorized_event


# Schema client services


class configuration(authorized_event):
    """A client requires a schema to validate data or display a form"""


class all(authorized_event):
    """A client requires a schema to validate data or display a form"""


class get(authorized_event):
    """A client requires a schema to validate data or display a form"""
