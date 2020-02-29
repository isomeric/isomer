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

Package: Provisions
===================

Initial client configuration data.
This contains tilelayer urls, api stuff etc.

"""

from isomer.logger import isolog, debug, warn  # , verbose, error, warn
from pkg_resources import iter_entry_points


def build_provision_store():
    available = {}

    for provision_entrypoint in iter_entry_points(group="isomer.provisions", name=None):
        isolog("Provisions found: ", provision_entrypoint.name, lvl=debug, emitter="DB")
        try:
            available[provision_entrypoint.name] = provision_entrypoint.load()
        except ImportError:
            isolog(
                "Problematic provision: ",
                provision_entrypoint.name,
                exc=True,
                lvl=warn,
                emitter="PROVISIONS",
                frame_ref=2,
            )

    isolog("Found provisions: ", sorted(list(available.keys())), emitter="PROVISIONS")
    # pprint(available)

    return available
