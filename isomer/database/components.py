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

"""Database maintenance components"""

import operator
import time
from os import walk, statvfs
from os.path import getsize, join

import pymongo
from circuits import Timer, Event

from isomer.component import ConfigurableComponent, handler
from isomer.database import dbhost, dbport, dbname
from isomer.database.backup import backup
from isomer.logger import verbose, error, warn
from isomer.misc.path import get_path


class Maintenance(ConfigurableComponent):
    """Regularly checks a few basic system maintenance tests like used
    storage space of collections and other data"""

    configprops = {
        "locations": {
            "type": "object",
            "properties": {
                "cache": {
                    "type": "object",
                    "properties": {
                        "minimum": {
                            "type": "integer",
                            "description": "Minimum free cache space to alert on",
                            "title": "Minimum cache space",
                            "default": 500 * 1024 * 1024,
                        }
                    },
                    "default": {},
                },
                "lib": {
                    "type": "object",
                    "properties": {
                        "minimum": {
                            "type": "integer",
                            "description": "Minimum free library space to alert on",
                            "title": "Minimum library space",
                            "default": 50 * 1024 * 1024,
                        }
                    },
                    "default": {},
                },
                "local": {
                    "type": "object",
                    "properties": {
                        "minimum": {
                            "type": "integer",
                            "description": "Minimum free local file storage "
                                           "space to alert on",
                            "title": "Minimum local storage space",
                            "default": 50 * 1024 * 1024,
                        }
                    },
                    "default": {},
                },
            },
            "default": {},
        },
        "interval": {
            "type": "integer",
            "title": "Check interval",
            "description": "Interval in seconds to check maintenance " "conditions",
            "default": 43200,
        },
    }

    def __init__(self, *args, **kwargs):
        super(Maintenance, self).__init__("MAINTENANCE", *args, **kwargs)
        self.log("Maintenance started")

        client = pymongo.MongoClient(dbhost, dbport)
        self.db = client[dbname]

        self.collection_sizes = {}
        self.collection_total = 0

        self.disk_allocated = {}
        self.disk_free = {}

        self.maintenance_check()
        self.timer = Timer(
            self.config.interval, Event.create("maintenance_check"), persist=True
        ).register(self)

    @handler("maintenance_check")
    def maintenance_check(self, *args):
        """Perform a regular maintenance check"""

        self.log("Performing maintenance check")
        self._check_collections()
        self._check_free_space()

    def _check_collections(self):
        """Checks node local collection storage sizes"""

        self.collection_sizes = {}
        self.collection_total = 0
        for col in self.db.list_collection_names():
            self.collection_sizes[col] = self.db.command("collstats", col).get(
                "storageSize", 0
            )
            self.collection_total += self.collection_sizes[col]

        sorted_x = sorted(self.collection_sizes.items(), key=operator.itemgetter(1))

        for item in sorted_x:
            self.log(
                "Collection size (%s): %.2f MB" % (item[0], item[1] / 1024.0 / 1024),
                lvl=verbose,
            )

        self.log(
            "Total collection sizes: %.2f MB" % (self.collection_total / 1024.0 / 1024)
        )

    def _check_free_space(self):
        """Checks used filesystem storage sizes"""

        def get_folder_size(path):
            """Aggregates used size of a specified path, recursively"""

            total_size = 0
            for item in walk(path):
                for file in item[2]:
                    try:
                        total_size = total_size + getsize(join(item[0], file))
                    except (OSError, PermissionError) as folder_size_e:
                        self.log("error with file:  " + join(item[0], file), folder_size_e)
            return total_size


        total = 0

        for name, checkpoint in self.config.locations.items():
            try:
                stats = statvfs(get_path(name, ""))
            except (OSError, PermissionError, KeyError) as e:
                self.log("Location unavailable:", name, e, type(e), lvl=warn, exc=True)
                continue
            free_space = stats.f_frsize * stats.f_bavail
            used_space = get_folder_size(get_path(name, "")) / 1024.0 / 1024
            total += used_space

            self.log("Location %s uses %.2f MB" % (name, used_space))

            if free_space < checkpoint["minimum"]:
                self.log(
                    "Short of free space on %s: %.2f MB left"
                    % (name, free_space / 1024.0 / 1024 / 1024),
                    lvl=warn,
                )

        self.log("Total space consumption: %.2f MB" % total)


class BackupManager(ConfigurableComponent):
    """Regularly creates backups of collections"""

    configprops = {
        "interval": {
            "type": "integer",
            "title": "Backup interval",
            "description": "Interval in seconds to create Backup",
            "default": 86400,
        }
    }

    def __init__(self, *args, **kwargs):
        super(BackupManager, self).__init__("BACKUP", *args, **kwargs)
        self.log("Backup manager started")

        self.timer = Timer(
            self.config.interval, Event.create("backup"), persist=True
        ).register(self)

    @handler("backup")
    def backup(self, *args):
        """Perform a regular backup"""

        self.log("Performing backup")
        self._create_backup()

    def _create_backup(self):
        self.log("Backing up all data")

        filename = time.strftime("%Y-%m-%d_%H%M%S.json")
        filename = join(get_path("local", "backup", ensure=True), filename)

        backup(None, None, None, "json", filename, False, True, [])
