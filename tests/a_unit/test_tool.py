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
Hackerfleet Operating System - Backend

Test Isomer Auth
==============



"""

import os
import pytest

from isomer.tool.tool import isotool


def test_tool_main():
    """Tests correct package importing"""

    import isomer.tool.tool

    cli = isomer.tool.tool.isotool

    assert cli is not None


def test_view_no_objects():
    """"""

    result = pytest.run_cli(isotool, [
        "--dbhost", pytest.DBHOST + ":" + pytest.DBPORT,
        "--dbname", pytest.DBNAME,
        'db', 'objects', 'view',
        "--schema", "systemconfig"
    ], full_log=True)

    assert result.exit_code == 0
    assert "Done: iso db objects view." in result.output



