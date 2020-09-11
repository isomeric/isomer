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

"""Database backup functionality"""

import json
from ast import literal_eval

import bson
import pymongo

from isomer.logger import isolog, debug, verbose, error, warn


def backup_log(*args, **kwargs):
    """Log as emitter 'BACKUP'"""
    kwargs.update({"emitter": "BACKUP", "frame_ref": 2})
    isolog(*args, **kwargs)


def dump(db_host, db_port, db_name, filename):
    """Dump a full database to JSON"""

    backup_log("Connecting database", db_host, db_port, db_name, lvl=debug)

    client = pymongo.MongoClient(host=str(db_host), port=int(db_port))
    db = client[str(db_name)]

    backup_log("Dumping data from database", db_name)

    content = []

    for collection_name in db.collection_names():
        backup_log("Archiving collection:", collection_name, lvl=debug)
        collection = db[collection_name]
        cursor = collection.find({})

        objects = []

        for document in cursor:
            backup_log(
                "Archiving:",
                document[:50] if len(document) >= 50 else document,
                lvl=verbose,
            )
            document["_id"] = str(document["_id"])
            objects.append(document)

        collection = {"collection": collection_name, "data": objects}
        content.append(collection)

    with open(filename, "w") as file:
        json.dump(content, file)

    backup_log("Done")

    return True


def load(db_host, db_port, db_name, filename):
    """Load a full database dump from JSON"""

    backup_log("Connecting database")

    client = pymongo.MongoClient(db_host, db_port)
    db = client[db_name]

    backup_log("Loading data")

    with open(filename, "r") as file:
        data = json.load(file)

    backup_log("Storing data to database")

    for import_item in data:
        collection_name = import_item["collection"]

        collection = db[collection_name]
        requests = []

        for document in import_item["data"]:
            document["_id"] = bson.ObjectId(document["_id"])
            requests.append(
                pymongo.ReplaceOne({"uuid": document["uuid"]}, document, upsert=True)
            )

        size = len(requests)

        if size > 0:
            collection.bulk_write(requests)
        backup_log(
            "Imported %i object%s into collection '%s'"
            % (size, "s" if size != 1 else "", collection_name)
        )

    backup_log("Done")

    return True


def backup(
    schema, uuid, export_filter, export_format, filename, pretty, export_all, omit
):
    """Exports all collections to (JSON-) files."""

    from isomer.database import objectmodels

    export_format = export_format.upper()

    if pretty:
        indent = 4
    else:
        indent = 0

    f = None

    if filename:
        try:
            f = open(filename, "w")
        except (IOError, PermissionError) as e:
            backup_log("Could not open output file for writing:", exc=True, lvl=error)
            return

    def output(what, convert=False):
        """Output the backup in a specified format."""

        if convert:
            if export_format == "JSON":
                data = json.dumps(what, indent=indent)
            else:
                data = ""
        else:
            data = what

        if not filename:
            # Do not use logger here! This data must go immediately to stdout.
            print(data)
        else:
            f.write(data)

    if schema is None:
        if export_all is False:
            backup_log("No schema given.", lvl=warn)
            return
        else:
            schemata = objectmodels.keys()
    else:
        schemata = [schema]

    all_items = {}

    for schema_item in schemata:
        model = objectmodels[schema_item]

        if uuid:
            obj = model.find({"uuid": uuid})
        elif export_filter:
            obj = model.find(literal_eval(export_filter))
        else:
            obj = model.find()

        items = []
        for item in obj:
            fields = item.serializablefields()
            for field in omit:
                try:
                    fields.pop(field)
                except KeyError:
                    pass
            items.append(fields)

        all_items[schema_item] = items

        # if pretty is True:
        #    output('\n// Objectmodel: ' + schema_item + '\n\n')
        # output(schema_item + ' = [\n')

    output(all_items, convert=True)

    if f is not None:
        f.flush()
        f.close()


def internal_restore(
    schema, uuid, object_filter, import_format, filename, all_schemata, dry
):
    """Foobar"""

    from isomer.database import objectmodels

    import_format = import_format.upper()

    if import_format == "JSON":
        with open(filename, "r") as f:
            json_data = f.read()
        data = json.loads(json_data)  # , parse_float=True, parse_int=True)
    else:
        backup_log("Importing non json data is WiP!", lvl=error)
        return

    if schema is None:
        if all_schemata is False:
            backup_log("No schema given. Read the help", lvl=warn)
            return
        else:
            schemata = data.keys()
    else:
        schemata = [schema]

    if object_filter is not None:
        backup_log("Object filtering on import is WiP! Ignoring for now.", lvl=warn)

    all_items = {}
    total = 0

    for schema_item in schemata:
        model = objectmodels[schema_item]

        objects = data[schema_item]
        items = []
        if uuid:
            for item in objects:
                if item["uuid"] == uuid:
                    items = [model(item)]
        else:
            for item in objects:
                thing = model(item)
                items.append(thing)

        schema_total = len(items)
        total += schema_total

        if dry:
            backup_log("Would import", schema_total, "items of", schema_item)
        all_items[schema_item] = items

    if dry:
        backup_log("Would import", total, "objects.")
    else:
        backup_log("Importing", total, "objects.")
        for schema_name, item_list in all_items.items():
            backup_log("Importing", len(item_list), "objects of type", schema_name)
            for item in item_list:
                item._fields["_id"] = bson.objectid.ObjectId(item._fields["_id"])
                item.save()
