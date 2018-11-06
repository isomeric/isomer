#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HFOS - Hackerfleet Operating System
# ===================================
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

import os.path
from os import makedirs
import click
from click_didyoumean import DYMGroup
from click_plugins import with_plugins

from pkg_resources import iter_entry_points

from isomer.logger import verbosity, warn, debug
from isomer.tool import log, db_host_default, db_host_help, db_host_metavar, db_default, db_help, db_metavar
from isomer.tool.etc import read_configuration, write_configuration, configuration_template


@click.group(context_settings={'help_option_names': ['-h', '--help']},
             cls=DYMGroup)
@click.option('--instance', default='default', help='Name of instance to act on',
              metavar='<name>')
@click.option('--quiet', default=False, help="Suppress all output",
              is_flag=True)
@click.option('--verbose', '-v', default=False, help="Give verbose output",
              is_flag=True)
@click.option('--log-level', '--log', default=20, help='Log level to use (0-100)',
              metavar='<number>')
@click.option('--dbhost', default=db_host_default, help=db_host_help,
              metavar=db_host_metavar)
@click.option('--dbname', default=db_default, help=db_help,
              metavar=db_metavar)
@click.option('--config', '-c', default='/etc/isomer/instances.conf',
              help='Specify configuration for instance management')
@click.pass_context
def cli(ctx, instance, quiet, verbose, log_level, dbhost, dbname, config):
    """Isomer Management Tool

    This tool supports various operations to manage isomer instances.

    Most of the commands are grouped. To obtain more information about the
    groups' available sub commands/groups, try

    iso [group]

    To display details of a command or its sub groups, try

    iso [group] [subgroup] [..] [command] --help

    To get a map of all available commands, try

    iso cmdmap
    """

    ctx.obj['instance'] = instance

    if dbname == db_default and instance != 'default':
        dbname = instance

    ctx.obj['quiet'] = quiet
    ctx.obj['verbose'] = verbose
    verbosity['console'] = log_level
    verbosity['global'] = log_level

    ctx.obj['dbhost'] = dbhost
    ctx.obj['dbname'] = dbname

    log('Loading configuration:', config, lvl=debug)

    if os.path.exists(config):
        ctx.obj['config'] = read_configuration(config)
        ctx.obj['config_filename'] = config
    else:
        log('Creating new configuration from template', lvl=verbose)

        base_directory = os.path.dirname(config)
        log('Base configuration directory:', base_directory, lvl=debug)

        if not os.path.exists(base_directory):
            try:
                makedirs(base_directory)
            except PermissionError:
                log('PermissionError: Could not create configuration directory "%s"' % base_directory, lvl=warn)
                return

        if write_configuration(config, configuration_template):
            ctx.obj['config'] = configuration_template
            ctx.obj['config_filename'] = config
        else:
            ctx.obj['config_filename'] = None


@with_plugins(iter_entry_points('isomer.management'))
@cli.group(cls=DYMGroup)
def plugin():
    """[GROUP] Plugin commands"""


cli.add_command(plugin)


