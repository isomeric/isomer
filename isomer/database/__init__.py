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


Module: Database
================

Contains the underlying object model manager and generates object factories
from schemata.

Contains
========

Objectstore builder functions.


"""

import sys
import formal
import jsonschema
import pymongo

from isomer import schemastore
from isomer.error import abort, abort, EXIT_NO_DATABASE
from isomer.logger import isolog, warn, critical, debug, verbose, error
from isomer.misc import std_color


def db_log(*args, **kwargs):
    """Log as emitter 'DB'"""
    kwargs.update({"emitter": "DB", "frame_ref": 2})
    isolog(*args, **kwargs)


objectmodels = None
collections = None

dbhost = ""
dbport = 0
dbname = ""
instance = ""
initialized = False
ValidationError = jsonschema.ValidationError


def clear_all():
    """DANGER!
    *This command is a maintenance tool and clears the complete database.*
    """

    sure = input(
        "Are you sure to drop the complete database content? (Type "
        "in upppercase YES)"
    )
    if not (sure == "YES"):
        db_log("Not deleting the database.")
        sys.exit()

    client = pymongo.MongoClient(host=dbhost, port=dbport)
    db = client[dbname]

    for col in db.collection_names(include_system_collections=False):
        db_log("Dropping collection ", col, lvl=warn)
        db.drop_collection(col)


class IsomerBaseModel(formal.formalModel):
    def save(self, *args, **kwargs):
        if self._fields.get("color", None) is None:
            self._fields["color"] = std_color()
        super(IsomerBaseModel, self).save(*args, **kwargs)

    @classmethod
    def by_uuid(cls, uuid):
        return cls.find_one({"uuid": uuid})


def _build_model_factories(store):
    """Generate factories to construct objects from schemata"""

    result = {}

    for schemaname in store:

        schema = None

        try:
            schema = store[schemaname]["schema"]
        except KeyError:
            db_log("No schema found for ", schemaname, lvl=critical, exc=True)

        try:
            result[schemaname] = formal.model_factory(schema, IsomerBaseModel)
        except Exception as e:
            db_log(
                "Could not create factory for schema ",
                schemaname,
                schema,
                lvl=critical,
                exc=True,
            )

    return result


def _build_collections(store):
    """Generate database collections with indices from the schemastore"""

    result = {}

    client = pymongo.MongoClient(host=dbhost, port=dbport)
    db = client[dbname]

    for schemaname in store:

        schema = None
        indices = None

        try:
            schema = store[schemaname]["schema"]
            indices = store[schemaname].get("indices", None)
        except KeyError:
            db_log("No schema found for ", schemaname, lvl=critical)

        try:
            result[schemaname] = db[schemaname]
        except Exception:
            db_log(
                "Could not get collection for schema ",
                schemaname,
                schema,
                lvl=critical,
                exc=True,
            )

        if indices is None:
            continue

        col = db[schemaname]
        db_log("Adding indices to", schemaname, lvl=debug)
        i = 0
        keys = list(indices.keys())

        while i < len(indices):
            index_name = keys[i]
            index = indices[index_name]

            index_type = index.get("type", None)
            index_unique = index.get("unique", False)
            index_sparse = index.get("sparse", True)
            index_reindex = index.get("reindex", False)

            if index_type in (None, "text"):
                index_type = pymongo.TEXT
            elif index_type == "2dsphere":
                index_type = pymongo.GEOSPHERE

            def do_index():
                col.ensure_index(
                    [(index_name, index_type)], unique=index_unique, sparse=index_sparse
                )

            db_log("Enabling index of type", index_type, "on", index_name, lvl=debug)
            try:
                do_index()
                i += 1
            except pymongo.errors.OperationFailure:
                db_log(col.list_indexes().__dict__, pretty=True, lvl=verbose)
                if not index_reindex:
                    db_log("Index was not created!", lvl=warn)
                    i += 1
                else:
                    try:
                        col.drop_index(index_name)
                        do_index()
                        i += 1
                    except pymongo.errors.OperationFailure as e:
                        db_log("Index recreation problem:", exc=True, lvl=error)
                        col.drop_indexes()
                        i = 0

                        # for index in col.list_indexes():
                        #    db_log("Index: ", index)
    return result


def initialize(
    address="127.0.0.1:27017",
    database_name="isomer-default",
    instance_name="default",
    reload=False,
    ignore_fail=False,
):
    """Initializes the database connectivity, schemata and finally object models"""

    global objectmodels
    global collections
    global dbhost
    global dbport
    global dbname
    global instance
    global initialized

    if initialized and not reload:
        isolog(
            "Already initialized and not reloading.",
            lvl=warn,
            emitter="DB",
            frame_ref=2,
        )
        return

    dbhost = address.split(":")[0]
    dbport = int(address.split(":")[1]) if ":" in address else 27017
    dbname = database_name

    db_log("Using database:", dbname, "@", dbhost, ":", dbport)

    try:
        client = pymongo.MongoClient(host=dbhost, port=dbport)
        db = client[dbname]
        db_log("Database: ", db.command("buildinfo"), lvl=debug)
    except Exception as e:
        log_level = warn if ignore_fail else critical
        db_log(
            "No database available! Check if you have mongodb > 2.2 "
            "installed and running as well as listening on port %i "
            "of %s and check if you specified the correct "
            "instance and environment. (Error: %s) -> EXIT" % (dbport, dbhost, e),
            lvl=log_level,
        )
        if not ignore_fail:
            abort(EXIT_NO_DATABASE)
        else:
            return False

    formal.connect(database_name, host=dbhost, port=dbport)
    formal.connect_sql(database_name, database_type="sql_memory")

    schemastore.schemastore = schemastore.build_schemastore_new()
    schemastore.l10n_schemastore = schemastore.build_l10n_schemastore(
        schemastore.schemastore
    )
    objectmodels = _build_model_factories(schemastore.schemastore)
    collections = _build_collections(schemastore.schemastore)
    instance = instance_name
    initialized = True

    return True
