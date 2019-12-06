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

Module: Configuration
=====================

Instance component configuration management.

"""

import json
import click

from ast import literal_eval
from click_didyoumean import DYMGroup

from formal import model_factory
from isomer.tool import log, finish


@click.group(cls=DYMGroup)
@click.pass_context
def config(ctx):
    """[GROUP] Configuration management operations"""

    from isomer import database

    database.initialize(ctx.obj["dbhost"], ctx.obj["dbname"])

    from isomer.schemata.component import ComponentConfigSchemaTemplate

    ctx.obj["col"] = model_factory(ComponentConfigSchemaTemplate)


@config.command(short_help="modify field values of component configurations")
@click.argument("component")
@click.argument("field")
@click.argument("value")
@click.pass_context
def modify(ctx, component, field, value):
    """Modify field values of objects"""
    col = ctx.obj["col"]

    configuration = get_configuration(col, component)

    if configuration is None:
        log("No component with that name or uuid found.")
        return

    log("Configuration found, modifying")
    try:
        new_value = literal_eval(value)
    except ValueError:
        log("Interpreting value as string")
        new_value = str(value)

    configuration._fields[field] = new_value
    configuration.validate()
    log("Changed configuration validated")
    configuration.save()
    finish(ctx)


@config.command(short_help="Enable a component")
@click.argument("component")
@click.pass_context
def enable(ctx, component):
    """Enable field values of objects"""

    col = ctx.obj["col"]

    configuration = get_configuration(col, component)

    if configuration is None:
        log("No component with that name or uuid found.")
        return

    log("Configuration found, enabling")

    configuration.active = True

    configuration.validate()
    configuration.save()
    finish(ctx)


@config.command(short_help="Disable a component")
@click.argument("component")
@click.pass_context
def disable(ctx, component):
    """Disable field values of objects"""

    col = ctx.obj["col"]

    configuration = get_configuration(col, component)

    if configuration is None:
        log("No component with that name or uuid found.")
        return

    log("Configuration found, disabling")

    configuration.active = False

    configuration.validate()
    configuration.save()
    finish(ctx)


@config.command(short_help="Delete component configuration")
@click.argument("component")
@click.pass_context
def delete(ctx, component):
    """Delete an existing component configuration. This will trigger
    the creation of its default configuration upon next restart."""
    col = ctx.obj["col"]

    log("Deleting component configuration", component, emitter="MANAGE")

    configuration = get_configuration(col, component)

    if configuration is None:
        log("No component with that name or uuid found.")
        return

    configuration.delete()
    finish(ctx)


@config.command(short_help="Show component configurations")
@click.option("--component", default=None)
@click.pass_context
def show(ctx, component):
    """Show the stored, active configuration of a component."""

    col = ctx.obj["col"]

    if col.count({"name": component}) > 1:
        log(
            "More than one component configuration of this name! Try "
            'one of the uuids as argument. Get a list with "config '
            'list"'
        )
        return

    if component is None:
        configurations = col.find()
        for configuration in configurations:
            log(
                "%-15s : %s" % (configuration.name, configuration.uuid),
                emitter="MANAGE",
            )
    else:
        configuration = get_configuration(col, component)

        if configuration is None:
            log("No component with that name or uuid found.")
            return

        print(json.dumps(configuration.serializablefields(), indent=4))


def get_configuration(col, component):
    """Get a configuration via name or uuid"""

    if col.count({"name": component}) > 1:
        log(
            "More than one component configuration of this name! Try "
            'one of the uuids as argument. Get a list with "config '
            'list"'
        )
        return

    configuration = col.find_one({"name": component})

    if configuration is None:
        configuration = col.find_one({"uuid": component})

    return configuration
