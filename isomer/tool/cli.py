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

Module: CLI
===========

Basic management tool functionality and plugin support.


"""

import os
import sys

import click
from click_didyoumean import DYMGroup
from click_plugins import with_plugins
from pkg_resources import iter_entry_points
from isomer.logger import set_logfile, set_color, set_verbosity, warn, verbose, \
    critical, debug
from isomer.misc.path import get_log_path, set_etc_path, set_instance, set_prefix_path
from isomer.tool import log, db_host_help, db_host_metavar, db_help, db_metavar
from isomer.tool.etc import (
    load_configuration,
    load_instances,
    instance_template,
    create_configuration,
)
from isomer.version import version_info

RPI_GPIO_CHANNEL = 5

@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    cls=DYMGroup,
    short_help="Main Isomer CLI"
)
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
@click.option("--no-log", default=False, is_flag=True, help="Do not log to file")
@click.option("--log-path", default=None, help="Logfile path")
@click.option("--log-file", default=None, help="Logfile name")
@click.option("--dbhost", default=None, help=db_host_help, metavar=db_host_metavar)
@click.option("--dbname", default=None, help=db_help, metavar=db_metavar)
@click.option("--prefix-path", "-p", default=None, help="Use different system prefix")
@click.option("--config-path", "-c", default="/etc/isomer",
              help="System configuration path")
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
        no_log,
        log_path,
        log_file,
        dbhost,
        dbname,
        prefix_path,
        config_path,
        fat_logo,
):
    """Isomer Management Tool

    This tool supports various operations to manage Isomer instances.

    Most of the commands are grouped. To obtain more information about the
    groups' available sub commands/groups, try

    iso [group]

    To display details of a command or its subgroups, try

    iso [group] [subgroup] [..] [command] --help

    To get a map of all available commands, try

    iso cmdmap
    """

    ctx.obj["quiet"] = quiet

    def _set_verbosity():
        if quiet:
            console_setting = 100
        else:
            console_setting = int(
                console_level if console_level is not None else 20
            )

        if no_log:
            file_setting = 100
        else:
            file_setting = int(file_level if file_level is not None else 20)

        global_setting = min(console_setting, file_setting)
        set_verbosity(global_setting, console_setting, file_setting)

    def _set_logger():
        if log_path is not None or log_file is not None:
            set_logfile(log_path, instance, log_file)

        if no_colors is False:
            set_color()

    _set_verbosity()
    _set_logger()

    ctx.obj["instance"] = instance

    log("Running with Python", sys.version.replace("\n", ""), sys.platform, lvl=verbose)
    log("Interpreter executable:", sys.executable, lvl=verbose)

    set_etc_path(config_path)
    configuration = load_configuration()

    if configuration is None:
        ctx = create_configuration(ctx)
        configuration = ctx.obj["config"]
    else:
        ctx.obj["config"] = configuration

    set_prefix_path(configuration['meta']['prefix'])

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
        instance_log_level = int(instance_configuration["loglevel"])

        set_verbosity(instance_log_level, file_level=instance_log_level)
        log("Instance log level set to", instance_log_level, lvl=verbose)

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

    def get_environment_toggle(platform, toggles):
        """Checks well known methods to determine if the other environment should be
        booted instead of the default environment."""

        def temp_file_toggle():
            """Check by looking for a state file in /tmp"""

            state_filename = "/tmp/isomer_toggle_%s" % instance_configuration["name"]
            log("Checking for override state file ", state_filename, lvl=debug)

            if os.path.exists(state_filename):
                log("Environment override state file found!", lvl=warn)
                return True
            else:
                log("Environment override state file not found", lvl=debug)
                return False

        def gpio_switch_toggle():
            """Check by inspection of a GPIO pin for a closed switch"""

            log("Checking for override GPIO switch on channel ", RPI_GPIO_CHANNEL,
                lvl=debug)

            if platform != "rpi":
                log(
                    "Environment toggle: "
                    "GPIO switch can only be handled on Raspberry Pi!",
                    lvl=critical
                )
                return False
            else:
                try:
                    import RPi.GPIO as GPIO
                except ImportError:
                    log("RPi Python module not found. "
                        "This only works on a Raspberry Pi!", lvl=critical)
                    return False

                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(RPI_GPIO_CHANNEL, GPIO.IN)

                state = GPIO.input(RPI_GPIO_CHANNEL) is True

                if state:
                    log("Environment override switch active!", lvl=warn)
                else:
                    log("Environment override switch not active", lvl=debug)

                return state

        toggle = False
        if "temp_file" in toggles:
            toggle = toggle or temp_file_toggle()
        if "gpio_switch" in toggles:
            toggle = toggle or gpio_switch_toggle()

        if toggle:
            log("Booting other Environment per user request.")
        else:
            log("Booting active environment", lvl=debug)

        return toggle

    #log(configuration['meta'], pretty=True)
    #log(instance_configuration, pretty=True)

    if get_environment_toggle(configuration["meta"]["platform"],
                              instance_configuration['environment_toggles']
                              ):
        if env == 'blue':
            env = 'green'
        else:
            env = 'blue'

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

    set_instance(instance, env, prefix_path)

    if log_path is None and log_file is None:
        log_path = get_log_path()

        set_logfile(log_path, instance, log_file)


@with_plugins(iter_entry_points("isomer.management"))
@cli.group(
    cls=DYMGroup,
    short_help="Plugin module management commands"
)
@click.pass_context
def module(ctx):
    """[GROUP] Module commands"""

    from isomer import database

    database.initialize(ctx.obj["dbhost"], ctx.obj["dbname"])
    ctx.obj["db"] = database


cli.add_command(module)
