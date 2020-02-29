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

Module: Migration
=================

"""

# from isomer.database import schemastore
from isomer.logger import isolog, warn, debug  # , error, verbose, critical
from deepdiff.diff import DeepDiff
from pkg_resources import iter_entry_points, DistributionNotFound
import dpath
import os

# import json

from pprint import pprint

MIGRATION_TEMPLATE = """#!/usr/bin/env python

# Migration template

"""


def log(*args, **kwargs):
    """Log as previous emitter"""
    kwargs.update({"frame_ref": 2})
    if "emitter" not in kwargs:
        kwargs["emitter"] = "MIGRATIONS"
    isolog(*args, **kwargs)


def make_migrations(schema=None):
    """Create migration data for a specified schema"""

    entrypoints = {}
    old = {}

    def apply_migrations(migrations, new_model):
        """Apply migration data to compile an up to date model"""

        def get_path(raw_path):
            """Get local path of schema definition"""

            print("RAW PATH:", raw_path, type(raw_path))
            path = []
            for item in raw_path.split("["):
                print(item)
                item = item.rstrip("]")
                item = item.replace('"', "")
                item = item.replace("'", "")
                try:
                    item = int(item)
                except ValueError:
                    pass
                path.append(item)
            path.remove("root")
            print("PATH:", path)
            return path

        def apply_entry(changetype, change, result):
            """Upgrade with a single migration"""

            def apply_removes(removes, result):
                """Delete removed fields"""

                for remove in removes:
                    path = get_path(remove)
                    amount = dpath.util.delete(result, path)
                    assert amount == 1
                return result

            def apply_additions(additions, result):
                """Add newly added fields"""

                for addition in additions:
                    path = get_path(addition)
                    entry = additions[addition]
                    log("Adding:", entry, "at", path)
                    dpath.util.new(result, path, entry)
                return result

            if changetype == "type_changes":
                log("Creating new object")
                result = change["root"]["new_value"]
                return result

            if changetype == "dictionary_item_added":
                log("Adding items")
                result = apply_additions(change, result)
            elif changetype == "dictionary_item_removed":
                log("Removing items")
                result = apply_removes(change, result)
            elif changetype == "values_changed":
                log("Changing items' types")
                for item in change:
                    path = get_path(item)
                    log(
                        "Changing",
                        path,
                        "from",
                        change[item]["old_value"],
                        " to",
                        change[item]["new_value"],
                    )
                    assert dpath.util.get(result, path) == change[item]["old_value"]
                    amount = dpath.util.set(result, path, change[item]["new_value"])
                    assert amount == 1

            return result

        def get_renames(migrations):
            """Check migrations for renamed fields"""

            log("Checking for rename operations:")
            # pprint(migrations)
            added = removed = None

            for entry in migrations:
                added = entry.get("dictionary_item_added", None)
                removed = entry.get("dictionary_item_removed", None)

            renames = []

            if added and removed:
                for addition in added:
                    path = get_path(addition)
                    for removal in removed:
                        removed_path = get_path(removal)
                        if path[:-1] == removed_path[:-1]:
                            log("Possible rename detected:", removal, "->", addition)
                            renames.append((removed_path, path))
            return renames

        result = {}
        for no, migration in enumerate(migrations):
            log("Migrating", no)
            log("Migration:", migration, lvl=debug)
            renamed = get_renames(migrations)

            for entry in migration:
                result = apply_entry(entry, migration[entry], result)

        pprint(result)
        return result

    def write_migration(schema, counter, path, previous, current):
        """Write out complete migration data"""

        filename = "%s_%04i.json" % (schema, counter)
        migration = DeepDiff(previous, current, verbose_level=2).to_json_pickle()
        if migration == "{}":
            log("Nothing changed - no new migration data.", lvl=warn)
            return

        print("Writing migration: ", os.path.join(path, filename))
        pprint(migration)

        with open(os.path.join(path, filename), "w") as f:
            f.write(migration)

    for schema_entrypoint in iter_entry_points(group="isomer.schemata", name=None):
        try:
            log("Schemata found: ", schema_entrypoint.name, lvl=debug)
            if schema is not None and schema_entrypoint.name != schema:
                continue

            entrypoints[schema_entrypoint.name] = schema_entrypoint
            pprint(schema_entrypoint.dist.location)
            schema_top = schema_entrypoint.dist.location
            schema_migrations = schema_entrypoint.module_name.replace(
                "schemata", "migrations"
            ).replace(".", "/")
            path = os.path.join(schema_top, schema_migrations)
            new_model = schema_entrypoint.load()["schema"]

            migrations = []

            try:
                for file in sorted(os.listdir(path)):
                    if not file.endswith(".json"):
                        continue
                    fullpath = os.path.join(path, file)
                    log("Importing migration", fullpath)
                    with open(fullpath, "r") as f:
                        migration = DeepDiff.from_json_pickle(f.read())
                    migrations.append(migration)
                    log("Successfully imported")

                if len(migrations) == 0:
                    raise ImportError
                pprint(migrations)
                model = apply_migrations(migrations, new_model)
                write_migration(schema, len(migrations) + 1, path, model, new_model)
            except ImportError as e:
                log("No previous migrations for", schema, e, type(e), exc=True)

            if len(migrations) == 0:
                write_migration(schema, 1, path, None, new_model)

        except (ImportError, DistributionNotFound) as e:
            log(
                "Problematic schema: ",
                e,
                type(e),
                schema_entrypoint.name,
                exc=True,
                lvl=warn,
            )

    log(
        "Found schemata: ", sorted(entrypoints.keys()), lvl=debug
    )

    log("Entrypoints:", entrypoints, pretty=True, lvl=debug)

    def make_single_migration(old, new):
        pass


def apply_migrations(ctx):
    """Apply migrations to a database"""
    log("Applying migrations is not implemented, yet.", lvl=warn)

    _ = ctx
