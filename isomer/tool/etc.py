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

Module: etc
===========

Instance, environment and remote configuration bits.

"""

import os
import glob

from tomlkit import loads, dumps
from tomlkit.exceptions import NonExistentKey
from tomlkit import document, table, nl, comment

from isomer.misc.std import std_now
from isomer.tool import log, error, debug, verbose, warn
from isomer.error import abort, EXIT_NO_PERMISSION
from isomer.misc.path import (
    get_etc_path,
    get_etc_instance_path,
    get_etc_remote_path,
    get_etc_remote_keys_path,
)

NonExistentKey = NonExistentKey


def create_configuration(ctx):
    """Creates an initial configuration"""
    log("Creating new configuration from template", lvl=verbose)

    if not os.path.exists(get_etc_path()):
        try:
            os.makedirs(get_etc_path())
            os.makedirs(get_etc_instance_path())
            os.makedirs(get_etc_remote_path())
            os.makedirs(get_etc_remote_keys_path())
        except PermissionError:
            log(
                'PermissionError: Could not create configuration directory "%s"'
                % get_etc_path(),
                lvl=warn,
            )
            abort(EXIT_NO_PERMISSION)

    write_configuration(configuration_template)
    ctx.obj["config"] = configuration_template

    return ctx


def write_configuration(config):
    """Write the main system configuration"""

    filename = os.path.join(get_etc_path(), "isomer.conf")

    try:
        with open(filename, "w") as f:
            f.write(dumps(config))
        log("Isomer configuration stored.", lvl=debug)
    except PermissionError:
        log(
            "PermissionError: Could not write instance management configuration file",
            lvl=error,
        )
        abort(EXIT_NO_PERMISSION)


def load_configuration():
    """Read the main system configuration"""

    filename = os.path.join(get_etc_path(), "isomer.conf")

    try:
        with open(filename, "r") as f:
            config = loads(f.read())
            log("Isomer configuration loaded.", lvl=debug)
    except FileNotFoundError:
        log("Configuration not found.", lvl=warn)
        return None

    return config


def valid_configuration(ctx):
    """Validates an isomer site configuration"""

    ports = []
    for name, item in ctx.obj["instances"].items():
        log("Valdiating instance", name, lvl=debug)
        log(item, pretty=True, lvl=verbose)
        if item["web_port"] in ports:
            log(
                "Duplicate web port found in instance: %s:%i"
                % (name, item["web_port"]),
                lvl=error,
            )
            return False
        else:
            ports.append(item["web_port"])

    return True


def load_instance(instance):
    """Read a single instance configuration"""

    file = os.path.join(get_etc_instance_path(), instance + ".conf")
    with open(file) as f:
        config = loads(f.read())
        log("Instance configuration'", instance, "'loaded.", lvl=debug)

    return config


def load_instances():
    """Read the instance configurations"""

    config = {}

    pattern = get_etc_instance_path() + "/*.conf"
    log("Loading all instance configuration files:", pattern, lvl=debug)

    for name in glob.glob(pattern):

        with open(name) as f:
            instance_name = os.path.basename(name).split(".")[0]
            config[instance_name] = loads(f.read())
            log("Instance configuration '", instance_name, "'loaded.", lvl=debug)

    return config


def write_instance(instance_configuration):
    """Write a new or updated instance"""

    instance_name = instance_configuration["name"]

    instance_file = os.path.join(
        get_etc_instance_path(), instance_name + ".conf"
    )
    instance_directory = os.path.join(get_etc_instance_path(), instance_name)
    try:
        log("Configuration:", instance_configuration, pretty=True, lvl=debug)
        with open(instance_file, "w") as f:
            f.write(dumps(instance_configuration))
        log("Instance configuration stored.", lvl=debug)

        if not os.path.exists(instance_directory):
            os.mkdir(instance_directory)
            log("Instance configuration directory created.", lvl=debug)
    except PermissionError:
        log(
            "PermissionError: Could not write instance management configuration "
            "file or create instance configuration directory.",
            lvl=error,
        )
        abort(EXIT_NO_PERMISSION)


def remove_instance(instance_configuration):
    """Remove the configuration file for an instance"""

    filename = os.path.join(get_etc_instance_path(), instance_configuration + ".conf")
    if os.path.exists(filename):
        log("Removing instance", instance_configuration)
        os.remove(filename)
    else:
        log("Instance not found.")


def load_remotes():
    """Read the remote system configurations"""

    config = {}

    for root, _, files in os.walk(get_etc_remote_path()):
        for file in files:
            with open(os.path.join(root, file)) as f:
                config[file.rstrip(".conf")] = loads(f.read())
                log("Remote configuration loaded.", lvl=debug)

    return config


def write_remote(remote):
    """Write a new or updated remote"""

    filename = os.path.join(get_etc_remote_path(), remote["name"] + ".conf")
    try:
        with open(filename, "w") as f:
            f.write(dumps(remote))
        log("Instance configuration stored.", lvl=debug)
    except PermissionError:
        log(
            "PermissionError: Could not write instance management configuration file",
            lvl=error,
        )
        abort(EXIT_NO_PERMISSION)


configuration_template = document()
configuration_template.add(comment("Isomer Instance Management Configuration"))
configuration_template.add(comment("Created on %s" % std_now()))
configuration_template.add(nl())

meta = table()
meta.add("platform", "amd64")
meta["platform"].comment("Set to rpi for advanced Raspberry Pi support")
meta.add("distribution", "debian")
meta["distribution"].comment("Currently, only debian supported")
meta.add("init", "systemd")
meta["init"].comment("Currently, only systemd supported")
meta.add("prefix", "")

configuration_template.add("meta", meta)

instance_template = table()
instance_template.add("name", "")
instance_template.add("contact", "")
instance_template.add("active", False)
instance_template.add("environment", "blue")
instance_template.add("environment_toggles", ["temp_file", "gpio_switch"])
instance_template.add("loglevel", "20")
instance_template.add("quiet", True)
instance_template.add("database_host", "localhost")
instance_template.add("database_port", 27017)
instance_template.add("database_type", "mongodb")
instance_template.add("user", "isomer")
instance_template.add("group", "isomer")
instance_template.add("web_address", "127.0.0.1")
instance_template["web_address"].comment("Local listening address of backend")
instance_template.add("web_hostnames", "localhost")
instance_template["web_hostnames"].comment("Comma separated list of FQDN hostnames."
    "Only the first one will be used for "
                                           "selfsigned certificates.")
instance_template.add("web_port", 8055)
instance_template.add("web_certificate", "")
instance_template.add("web_key", "")
# TODO: Fix this comment and make the web_certificate stuff a table
instance_template.comment("These certificate details are only for selfsigned "
                          "certificates:")
instance_template.add("web_certificate_issuer", "Isomeric Community")
instance_template.add("web_certificate_unit", "Unknown")
instance_template.add("web_certificate_country", "EU")
instance_template.add("web_certificate_state", "Unknown")
instance_template.add("web_certificate_location", "Unknown")
instance_template.add("source", "")
instance_template["source"].comment("git, link or copy")
instance_template.add("url", "")
instance_template.add("modules", [])
instance_template["modules"].comment("Modules added as [method, url] items")

instance_template["database_type"].comment("Currently, only mongodb supported")
instance_template.add("webserver", "nginx")
instance_template["webserver"].comment("Currently, only nginx supported")
instance_template.add("service_template", "builtin")
instance_template["service_template"].comment(
    "Currently, only a builtin one supported"
)

environment_template = table()
environment_template.add("version", "")
environment_template.add("old_version", "")
environment_template.add("database", "")
environment_template.add("modules", {})
environment_template.add("blacklist", [])
environment_template.add("installed", False)
environment_template.add("provisioned", False)
environment_template.add("migrated", False)
environment_template.add("frontend", False)
environment_template.add("tested", False)
environment_template.add("approved", False)

environments = table()
blue = environment_template
green = environment_template

environments.add("blue", blue)
environments.add("green", green)

archive = table()

environments.add("archive", archive)

instance_template.add("environments", environments)

remote_template = document()
remote_template.add(comment("Isomer Remote Instance Configuration"))
remote_template.add(comment("Created on %s" % std_now()))
remote_template.add(nl())

remote_template.add("platform", "")
remote_template.add("name", "")
remote_template.add("use_sudo", False)
remote_template.add("source", "")
remote_template.add("url", "")

login_table = table()

login_table.add("hostname", "")
login_table.add("password", "")
login_table.add("username", "")
login_table.add("private_key_file", "")
login_table.add("port", 22)

remote_template.add("login", login_table)
