#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2018 Heiko 'riot' Weinen <riot@c-base.org> and others.
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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import click

from isomer.database import backup as internal_backup, internal_restore
from isomer.tool.database import db


@db.command('export', short_help='export objects to json')
@click.option("--schema", "-s", default=None, help="Specify schema to export")
@click.option("--uuid", "-u", default=None, help="Specify single object to export")
@click.option("--object-filter", "--filter", default=None, help="Find objects to export by filter")
@click.option("--export-format", "--format", default='json', help="Currently only JSON is supported")
@click.option("--pretty", "-p", default=False, is_flag=True, help="Indent output for human readability")
@click.option("--all-schemata", "--all", default=False, is_flag=True,
              help="Agree to export all documents, if no schema specified")
@click.option("--omit", "-o", multiple=True, default=[], help="Omit given fields (multiple, e.g. '-o _id -o perms')")
@click.argument("filename")
def db_export(schema, uuid, object_filter, export_format, filename, pretty, all_schemata, omit):
    """Export stored objects

    Warning! This functionality is work in progress and you may destroy live data by using it!
    Be very careful when using the export/import functionality!"""

    internal_backup(schema, uuid, object_filter, export_format, filename, pretty, all_schemata, omit)


@db.command('import', short_help='import objects from json')
@click.option("--schema", default=None, help="Specify schema to import")
@click.option("--uuid", default=None, help="Specify single object to import")
@click.option("--object-filter", "--filter", default=None,
              help="Specify objects to import by filter (Not implemented yet!)")
@click.option("--import-format", "--format", default='json', help="Currently only JSON is supported")
@click.option("--filename", default=None, help="Import from given file")
@click.option("--all-schemata", "--all", default=False, is_flag=True,
              help="Agree to import all documents, if no schema specified")
@click.option("--dry", default=False, is_flag=True, help="Do not write changes to the database")
@click.pass_context
def db_import(ctx, schema, uuid, object_filter, import_format, filename, all_schemata, dry):
    """Import objects from file

    Warning! This functionality is work in progress and you may destroy live data by using it!
    Be very careful when using the export/import functionality!"""

    internal_restore(schema, uuid, object_filter, import_format, filename, all_schemata, dry)


