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
Hackerfleet Operating System - Backend

Test Isomer Auth
==============



"""

from circuits import Manager, Event
import pytest
from isomer.ui.auth import Authenticator
from isomer.events.client import authenticationrequest, authentication
from isomer.misc import std_uuid, std_now, std_hash
from isomer.database import objectmodels
import isomer.logger as logger


def test_package():
    """Tests correct package importing"""

    import isomer

    assert isomer is not None

