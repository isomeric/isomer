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

Module: tool
============

Assembly of all Isomer tool functionality.

"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from isomer.tool.configuration import config
from isomer.tool.backup import db_export, db_import
from isomer.tool.database import db

from isomer.tool.objects import objects
from isomer.tool.installer import install
from isomer.tool.instance import instance
from isomer.tool.environment import environment
from isomer.tool.system import system
from isomer.tool.rbac import rbac
from isomer.tool.user import user
from isomer.tool.remote import remote
from isomer.tool.misc import cmdmap, shell
from isomer.tool.dev import dev
from isomer.tool.cli import cli
from isomer.launcher import launch

cli.add_command(instance)
cli.add_command(environment)
cli.add_command(system)
cli.add_command(config)
cli.add_command(install)
cli.add_command(cmdmap)
cli.add_command(shell)
cli.add_command(remote)
cli.add_command(dev)

db.add_command(rbac)
db.add_command(objects)
db.add_command(db_export)
db.add_command(db_import)
db.add_command(user)

cli.add_command(db)

cli.add_command(launch)

isotool = cli
