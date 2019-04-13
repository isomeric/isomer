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

Module: CLI
===========

Basic management tool functionality and plugin support.


"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import sys
import click

from click_didyoumean import DYMGroup
from click_plugins import with_plugins

from pkg_resources import iter_entry_points

from isomer.logger import set_logfile, set_color, verbosity, warn, verbose
from isomer.misc.path import get_log_path, set_etc_path, set_instance
from isomer.tool import log, db_host_help, db_host_metavar, db_help, db_metavar
from isomer.tool.etc import (
    load_configuration,
    load_instances,
    instance_template,
    create_configuration,
)
from isomer.version import version_info


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, cls=DYMGroup)
@click.option(
    "--instance",
    "-i",
    default="default",
    help="Name of instance to act on",
    metavar="<name>",
)
@click.option(
    "--env",
    "--environment",
    "-e",
    help="Override environment to act on (CAUTION!)",
    default=None,
    type=click.Choice(["blue", "green", "current", "other"]),
)
@click.option("--quiet", default=False, help="Suppress all output", is_flag=True)
@click.option(
    "--no-colors", "-nc", default=False, help="Do not use colorful output", is_flag=True
)
@click.option(
    "--console-level",
    "--clog",
    default=None,
    help="Log level to use (0-100)",
    metavar="<level>",
)
@click.option(
    "--file-level",
    "--flog",
    default=None,
    help="Log level to use (0-100)",
    metavar="<level>",
)
@click.option("--do-log", default=False, is_flag=True, help="Log to file")
@click.option("--log-path", default=None, help="Logfile path")
@click.option("--dbhost", default=None, help=db_host_help, metavar=db_host_metavar)
@click.option("--dbname", default=None, help=db_help, metavar=db_metavar)
@click.option("--prefix", default=None, help="Use different system prefix")
@click.option("--config-dir", "-c", default="/etc/isomer")
@click.option("--fat-logo", "--fat", hidden=True, is_flag=True, default=False)
@click.pass_context
def cli(
    ctx,
    instance,
    env,
    quiet,
    no_colors,
    console_level,
    file_level,
    do_log,
    log_path,
    dbhost,
    dbname,
    prefix,
    config_dir,
    fat_logo,
):
    """Isomer Management Tool

    This tool supports various operations to manage Isomer instances.

    Most of the commands are grouped. To obtain more information about the
    groups' available sub commands/groups, try

    iso [group]

    To display details of a command or its sub groups, try

    iso [group] [subgroup] [..] [command] --help

    To get a map of all available commands, try

    iso cmdmap
    """

    ctx.obj["quiet"] = quiet

    def set_verbosity():
        if quiet:
            verbosity["console"] = 100
        else:
            verbosity["console"] = int(
                console_level if console_level is not None else 20
            )

        if do_log:
            verbosity["file"] = int(file_level if file_level is not None else 20)
        else:
            verbosity["file"] = 100

        verbosity["global"] = min(verbosity["console"], verbosity["file"])

    def set_logger():
        if log_path is not None:
            set_logfile(log_path, instance)

        if no_colors is False:
            set_color()

    set_verbosity()
    set_logger()

    ctx.obj["instance"] = instance

    log("Running with Python", sys.version.replace("\n", ""), sys.platform, lvl=verbose)
    log("Interpreter executable:", sys.executable, lvl=verbose)

    set_etc_path(config_dir)
    configuration = load_configuration()

    if configuration is None:
        ctx = create_configuration(ctx)
    else:
        ctx.obj["config"] = configuration

    # set_prefix(configuration['meta']['prefix'])

    instances = load_instances()

    ctx.obj["instances"] = instances

    if instance not in instances:
        log(
            "No instance configuration called %s found! Using fresh defaults."
            % instance,
            lvl=warn,
        )
        instance_configuration = instance_template
    else:
        instance_configuration = instances[instance]

    if file_level is None and console_level is None:
        # TODO: There is a bug here preventing the log-level to be set correctly.
        verbosity["file_level"] = int(instance_configuration["loglevel"])
        verbosity["global"] = int(instance_configuration["loglevel"])
        log("Log level set to", verbosity["global"], lvl=verbose)

    ctx.obj["instance_configuration"] = instance_configuration

    instance_environment = instance_configuration["environment"]

    if env is not None:
        if env == "current":
            ctx.obj["acting_environment"] = instance_environment
        elif env == "other":
            ctx.obj["acting_environment"] = (
                "blue" if instance_environment == "green" else "blue"
            )
        else:
            ctx.obj["acting_environment"] = env
        env = ctx.obj["acting_environment"]
    else:
        env = instance_configuration["environment"]
        ctx.obj["acting_environment"] = None

    ctx.obj["environment"] = env

    if not fat_logo:
        log("<> Isomer", version_info, " [%s|%s]" % (instance, env), lvl=99)
    else:
        from isomer.misc import logo

        pad = len(logo.split("\n", maxsplit=1)[0])
        log(("Isomer %s" % version_info).center(pad), lvl=99)
        for line in logo.split("\n"):
            log(line, lvl=99)

    if dbname is None:
        dbname = instance_configuration["environments"][env]["database"]
        if dbname in ("", None) and ctx.invoked_subcommand in (
            "config",
            "db",
            "environment",
            "plugin",
        ):
            log(
                "Database for this instance environment is unset, "
                "you probably have to install the environment first.",
                lvl=warn,
            )

    if dbhost is None:
        dbhost = "%s:%i" % (
            instance_configuration["database_host"],
            instance_configuration["database_port"],
        )

    ctx.obj["dbhost"] = dbhost
    ctx.obj["dbname"] = dbname

    set_instance(instance, env, prefix)

    if log_path is None:
        log_path = get_log_path()

        set_logfile(log_path, instance)


@with_plugins(iter_entry_points("isomer.management"))
@cli.group(cls=DYMGroup)
def plugin():
    """[GROUP] Plugin commands"""


cli.add_command(plugin)
