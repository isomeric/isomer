#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 riot <riot@c-base.org> and others.
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

Isomer Management Tool
======================

This is the management tool to install, configure and maintain
Isomer instances.

"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import sys

if sys.version_info.major < 3:
    print('The iso test tool has been evoked with an older Python version. '
          'Please restart the iso test tool to use Python3.')
    sys.exit()

from isomer.tool import install_isomer, ask
from isomer.tool.tool import isotool
from isomer.logger import isolog

isolog("Ok.", emitter="ISOTEST")
