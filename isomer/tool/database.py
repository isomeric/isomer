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

Database management functionality.

"""

import click
import pymongo
from click_didyoumean import DYMGroup

from isomer.logger import warn, error
from isomer.migration import make_migrations
from isomer.tool import log, ask, finish
from isomer.error import abort


@click.group(cls=DYMGroup)
@click.pass_context
def db(ctx):
    """[GROUP] Database management operations"""

    # log(ctx.obj, pretty=True)
    from isomer import database

    ignore_fail = ctx.invoked_subcommand in ("list-all", "rename", "delete")

    database.initialize(ctx.obj["dbhost"], ctx.obj["dbname"], ignore_fail=ignore_fail)
    ctx.obj["db"] = database


@db.command(short_help="List all mongodb databases")
@click.pass_context
def list_all(ctx):
    """List all available Mongo Databases on the configured database host."""
    from pymongo import MongoClient

    client = MongoClient(ctx.obj["dbhost"])
    log(client.list_database_names())

    finish(ctx)


@db.command(short_help="Rename database")
@click.argument("source")
@click.argument("destination")
@click.option("--keep", is_flag=True, help="Keep original database", default=False)
@click.option(
    "--clear-target", is_flag=True, help="Erase target if it exists", default=False
)
@click.pass_context
def rename(ctx, source, destination, keep, clear_target):
    """Rename Mongodb databases"""

    from pymongo import MongoClient

    client = MongoClient(ctx.obj["dbhost"])

    if source not in client.list_database_names():
        log("Source database", source, "does not exist!", lvl=warn)
        abort(-1)

    database = client.admin
    log("Copying", source, "to", destination)

    if destination in client.list_database_names():
        log("Destination exists")
        if clear_target:
            log("Clearing")
            client.drop_database(destination)
        else:
            log("Not destroying existing data", lvl=warn)
            abort(-1)

    database.command("copydb", fromdb=source, todb=destination)

    if not keep:
        log("Deleting old database")
        client.drop_database(source)

    finish(ctx)


@db.command(short_help="Irrevocably remove collection content")
@click.argument("schema")
@click.pass_context
def clear(ctx, schema):
    """Clears an entire database collection irrevocably. Use with caution!"""

    response = ask(
        'Are you sure you want to delete the collection "%s"' % schema,
        default="N",
        data_type="bool",
    )
    if response is True:
        host, port = ctx.obj["dbhost"].split(":")

        client = pymongo.MongoClient(host=host, port=int(port))
        database = client[ctx.obj["dbname"]]

        log("Clearing collection for", schema, lvl=warn, emitter="MANAGE")
        result = database.drop_collection(schema)
        if not result["ok"]:
            log("Could not drop collection:", lvl=error)
            log(result, pretty=True, lvl=error)
        else:
            finish(ctx)


@db.command(short_help="Irrevocably remove database")
@click.option(
    "--force",
    "-f",
    help="Force deletion without user intervention",
    is_flag=True,
    default=False,
)
@click.pass_context
def delete(ctx, force):
    """Deletes an entire database irrevocably. Use with extreme caution!"""

    delete_database(ctx.obj["dbhost"], ctx.obj["dbname"], force)

    finish(ctx)


def delete_database(db_host, db_name, force):
    """Actually delete a database"""

    if force:
        response = True
    else:
        response = ask(
            'Are you sure you want to delete database "%s"' % db_name,
            default="N",
            data_type="bool",
        )
    if response is True:
        host, port = db_host.split(":")

        client = pymongo.MongoClient(host=host, port=int(port))
        if db_name in client.list_database_names():
            log("Dropping database", db_name, lvl=warn)
            client.drop_database(db_name)
        else:
            log("Database does not exist")


@db.command(short_help="Copy a database")
@click.option(
    "--source", "-s", default=None,
    help="Specify source database. "
         "Leave out to use the default instance's active database."
)
@click.argument("destination")
@click.pass_context
def copy(ctx, source, destination):
    """Copies an entire database"""

    if source is None:
        source = ctx.obj["dbname"]

    copy_database(ctx.obj["dbhost"], source, destination)

    finish(ctx)


def copy_database(db_host, source, destination):
    """Actually copy a database"""

    host, port = db_host.split(":")

    client = pymongo.MongoClient(host=host, port=int(port))
    client.admin.command('copydb', fromdb=source, todb=destination)


@db.group(cls=DYMGroup)
@click.option("--schema", help="Specify schema to work with", default=None)
@click.pass_context
def migrations(ctx, schema):
    """[GROUP] Data migration management"""

    ctx.obj["schema"] = schema


@migrations.command(short_help="make new migrations")
@click.pass_context
def make(ctx):
    """Makes new migrations for all or the specified schema"""

    make_migrations(ctx.obj["schema"])

    finish(ctx)
