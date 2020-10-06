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

import formal


from isomer.logger import debug, warn
from isomer.database import db_log
from isomer.schemastore import schemastore

from pprint import pprint


def profile(schemaname="sensordata", profiletype="pjs"):
    """Profiles object model handling with a very simple benchmarking test"""

    db_log("Profiling ", schemaname)

    schema = schemastore[schemaname]["schema"]

    db_log("Schema: ", schema, lvl=debug)

    testclass = None

    if profiletype == "formal":
        db_log("Running formal benchmark")
        testclass = formal.model_factory(schema)
    elif profiletype == "pjs":
        db_log("Running PJS benchmark")
        try:
            import python_jsonschema_objects as pjs
        except ImportError:
            db_log(
                "PJS benchmark selected but not available. Install "
                "python_jsonschema_objects (PJS)"
            )
            return

        db_log()
        builder = pjs.ObjectBuilder(schema)
        ns = builder.build_classes()
        pprint(ns)
        testclass = ns[schemaname]
        db_log("ns: ", ns, lvl=warn)

    if testclass is not None:
        db_log("Instantiating elements...")
        for i in range(100):
            testclass()
    else:
        db_log("No Profiletype available!")

    db_log("Profiling done")


# profile(schemaname='sensordata', profiletype='formal')
