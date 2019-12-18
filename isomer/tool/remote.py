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

Module: remote
==============

Remote instance management functionality.

This module allows deploying and maintaining instances on remote systems via SSH.

"""

import os
import sys
import spur
import tomlkit
import click
import getpass

from binascii import hexlify

from isomer.logger import warn, error, debug, verbose
from isomer.misc import std_now
from isomer.tool import (
    log,
    run_process,
    install_isomer,
    get_isomer,
    format_result,
)  # , ask_password
from isomer.misc.path import get_etc_remote_keys_path
from isomer.tool.defaults import platforms, key_defaults
from isomer.error import abort, EXIT_INVALID_PARAMETER, EXIT_INVALID_VALUE
from isomer.tool.cli import cli
from isomer.tool.etc import load_remotes, remote_template, write_remote

try:
    from paramiko import DSSKey, RSAKey

    key_dispatch_table = {"dsa": DSSKey, "rsa": RSAKey}
except ImportError:
    key_dispatch_table = None


def get_remote_home(username):
    """Expands a username into a correct home directory"""

    if username == "root":
        return "/root/"
    else:
        return "/home/" + username


@cli.group()
@click.option("--name", "-n", default="default")
@click.option("--install", "-i", is_flag=True, default=False)
@click.option(
    "--platform",
    "-p",
    default=list(platforms.keys())[0],
    type=click.Choice(platforms.keys()),
)
@click.option(
    "--source", "-s", default="git", type=click.Choice(["link", "copy", "git"])
)
@click.option("--url", "-u", default=None)
@click.option("--existing", "-e", default=None)
@click.pass_context
def remote(ctx, name, install, platform, source, url, existing):
    """Remote instance control (Work in Progress!)"""

    ctx.obj["remote"] = name
    ctx.obj["platform"] = platform
    ctx.obj["source"] = source
    ctx.obj["url"] = url
    ctx.obj["existing"] = existing

    if ctx.invoked_subcommand == "add":
        return

    remotes = ctx.obj["remotes"] = load_remotes()

    if ctx.invoked_subcommand == "list":
        return

    # log('Remote configurations:', remotes, pretty=True)

    host_config = remotes.get(name, None)

    if host_config is None:
        log("Cannot proceed, remote unknown", lvl=error)
        abort(5000)

    ctx.obj["host_config"] = host_config

    if platform is None:
        platform = ctx.obj["host_config"].get("platform", "debian")
    ctx.obj["platform"] = platform

    spur_config = dict(host_config["login"])

    if spur_config["private_key_file"] == "":
        spur_config.pop("private_key_file")

    if spur_config["port"] != 22:
        log(
            "Warning! Using any port other than 22 is not supported right now.",
            lvl=warn,
        )

    spur_config.pop("port")

    shell = spur.SshShell(**spur_config)

    if install:
        success, result = run_process("/", ["iso", "info"], shell)
        if success:
            log("Isomer version on remote:", format_result(result))
        else:
            log('Use "remote install" for now')
            # if existing is None:
            #     get_isomer(source, url, '/root', shell=shell)
            #     destination = '/' + host_config['login']['username'] + '/repository'
            # else:
            #     destination = existing
            # install_isomer(platform, host_config.get('use_sudo', True), shell, cwd=destination)

    ctx.obj["shell"] = shell


@remote.command()
@click.argument("hostname")
@click.option(
    "--username",
    "-u",
    prompt=True,
    default=lambda: os.environ.get("USER", ""),
    show_default="current user",
)
@click.option("--password", "-pw", default="")
@click.option("--port", "-p", default=22)
@click.option("--use-sudo", "-s", default=False, is_flag=True)
@click.option("--make-key", "-m", default=False, is_flag=True)
@click.option("--key-file", "-k", default="")
@click.option(
    "--key-type",
    "-t",
    default=key_defaults["type"],
    help="Key type (%s)" % key_defaults["type"],
    type=click.Choice(["dsa", "rsa"]),
)
@click.option(
    "--key-bits",
    "-b",
    default=key_defaults["bits"],
    help="Key bits (%i)" % key_defaults["bits"],
)
@click.pass_context
def add(
    ctx,
    hostname,
    username,
    password,
    port,
    use_sudo,
    make_key,
    key_file,
    key_type,
    key_bits,
):
    """Adds a new remote"""

    if make_key:
        if key_dispatch_table is None:
            log(
                "You'll need to install paramiko to generate remote keys. Use pip3 install paramiko",
                lvl=error,
            )
            abort(5000)

        if key_file == "":
            key_file = os.path.join(get_etc_remote_keys_path(), ctx.obj["remote"])

        phrase = None

        if key_type == "dsa" and key_bits > 1024:
            log("DSA Keys must be 1024 bits", lvl=error)
            abort(5000)

        # generating private key
        prv = key_dispatch_table[key_type].generate(bits=key_bits, progress_func=log)
        prv.write_private_key_file(key_file, password=phrase)
        # generating public key
        pub = key_dispatch_table[key_type](filename=key_file, password=phrase)
        with open("%s.pub" % key_file, "w") as f:
            f.write("%s %s" % (pub.get_name(), pub.get_base64()))
            f.write(" %s" % key_defaults["comment"])

        key_hash = hexlify(pub.get_fingerprint())
        log(
            "Fingerprint: %d %s %s.pub (%s)"
            % (
                key_bits,
                ":".join(
                    [str(key_hash)[i: 2 + i] for i in range(0, len(key_hash), 2)]
                ),
                key_file,
                key_type.upper(),
            )
        )

    new_remote = remote_template
    new_remote["name"] = ctx.obj["remote"]
    new_remote["platform"] = ctx.obj["platform"]
    new_remote["use_sudo"] = use_sudo
    new_remote["source"] = ctx.obj["source"]
    new_remote["url"] = ctx.obj["url"]

    new_remote["login"]["hostname"] = hostname
    new_remote["login"]["username"] = username
    new_remote["login"]["password"] = password
    new_remote["login"]["port"] = port
    new_remote["login"]["private_key_file"] = key_file

    log("New remote:", new_remote, pretty=True)
    write_remote(new_remote)


@remote.command()
@click.option(
    "--accept",
    "-a",
    help="Accept missing host key and add it to known_hosts",
    is_flag=True,
    default=False,
)
@click.pass_context
def upload_key(ctx, accept):
    """Upload a remote key to a user account on a remote machine"""

    login_config = dict(ctx.obj["host_config"]["login"])

    if login_config["password"] == "":
        login_config["password"] = getpass.getpass()

    with open(login_config["private_key_file"] + ".pub") as f:
        key = f.read()

    username = login_config["username"]

    if accept:
        host_key_flag = spur.ssh.MissingHostKey.warn
    else:
        host_key_flag = spur.ssh.MissingHostKey.raise_error

    shell = spur.SshShell(
        hostname=login_config["hostname"],
        username=login_config["username"],
        password=login_config["password"],
        missing_host_key=host_key_flag,
    )

    try:
        with shell.open("/home/" + username + "/.ssh/authorized_keys", "r") as f:
            result = f.read()
    except spur.ssh.ConnectionError as e:
        log("SSH Connection error:\n", e, lvl=error)
        log(
            "Host not in known hosts or other problem. Use --accept to add to known_hosts."
        )
        abort(50071)
    except FileNotFoundError as e:
        log("No authorized key file yet, creating")
        success, result = run_process(
            "/home/" + username,
            ["/bin/mkdir", "/home/" + username + "/.ssh"],
            shell=shell,
        )
        if not success:
            log(
                "Error creating .ssh directory:",
                e,
                format_result(result),
                pretty=True,
                lvl=error,
            )
        success, result = run_process(
            "/home/" + login_config["username"],
            ["/usr/bin/touch", "/home/" + username + "/.ssh/authorized_keys"],
            shell=shell,
        )
        if not success:
            log(
                "Error creating authorized hosts file:",
                e,
                format_result(result).output,
                lvl=error,
            )
        result = ""

    if key not in result:
        log("Key not yet authorized - adding")
        with shell.open("/home/" + username + "/.ssh/authorized_keys", "a") as f:
            f.write(key)
    else:
        log("Key is already authorized.", lvl=warn)

    log("Uploaded key")


@remote.command(name="set", short_help="Set a parameter of a remote")
@click.option(
    "--login", "-l", help="Modify login settings", is_flag=True, default=False
)
@click.argument("parameter")
@click.argument("value")
@click.pass_context
def set_parameter(ctx, login, parameter, value):
    """Set a configuration parameter of an instance"""

    log("Setting %s to %s" % (parameter, value))
    remote_config = ctx.obj["host_config"]
    defaults = remote_template

    converted_value = None

    try:
        if login:
            parameter_type = type(defaults["login"][parameter])
        else:
            parameter_type = type(defaults[parameter])

        log(parameter_type, pretty=True, lvl=verbose)

        if parameter_type == tomlkit.api.Integer:
            converted_value = int(value)
        else:
            converted_value = value
    except KeyError:
        log(
            "Invalid parameter specified. Available parameters:",
            sorted(list(defaults.keys())),
            lvl=warn,
        )
        abort(EXIT_INVALID_PARAMETER)

    if converted_value is None:
        abort(EXIT_INVALID_VALUE)

    if login:
        remote_config["login"][parameter] = converted_value
    else:
        remote_config[parameter] = converted_value

    log("New config:", remote_config, pretty=True, lvl=debug)

    ctx.obj["remotes"][ctx.obj["remote"]] = remote_config

    write_remote(remote_config)


@remote.command(name="install")
@click.option(
    "--archive", "-a", is_flag=True, default=False, help="Archive existing Isomer first"
)
@click.option(
    "--setup",
    "-s",
    is_flag=True,
    default=False,
    help="Setup basic Isomer user/directories",
)
@click.pass_context
def install_remote(ctx, archive, setup):
    """Installs Isomer (Management) on a remote host"""

    shell = ctx.obj["shell"]
    platform = ctx.obj["platform"]
    host_config = ctx.obj["host_config"]
    use_sudo = host_config["use_sudo"]
    username = host_config["login"]["username"]
    existing = ctx.obj["existing"]
    remote_home = get_remote_home(username)
    target = os.path.join(remote_home, "isomer")

    log(remote_home)

    if shell is None:
        log("Remote was not configured properly.", lvl=warn)
        abort(5000)

    if archive:
        log("Renaming remote isomer copy")
        success, result = run_process(
            remote_home,
            ["mv", target, os.path.join(remote_home, "isomer_" + std_now())],
            shell=shell,
        )
        if not success:
            log("Could not rename remote copy:", result, pretty=True, lvl=error)
            abort(5000)

    if existing is None:
        url = ctx.obj["url"]
        if url is None:
            url = host_config.get("url", None)

        source = ctx.obj["source"]
        if source is None:
            source = host_config.get("source", None)

        if url is None or source is None:
            log('Need a source and url to install. Try "iso remote --help".')
            abort(5000)

        get_isomer(source, url, target, upgrade=ctx.obj["upgrade"], shell=shell)
        destination = os.path.join(remote_home, "isomer")
    else:
        destination = existing

    install_isomer(platform, use_sudo, shell=shell, cwd=destination)

    if setup:
        log("Setting up system user and paths")
        success, result = run_process(remote_home, ["iso", "system", "all"])
        if not success:
            log(
                "Setting up system failed:",
                format_result(result),
                pretty=True,
                lvl=error,
            )


@remote.command()
@click.pass_context
def upgrade(ctx):
    """Upgrade an existing remote"""

    ctx.obj["archive"] = True
    ctx.obj["setup"] = False
    ctx.obj["upgrade"] = True
    ctx.forward(install_remote)


@remote.command()
@click.pass_context
def info(ctx):
    """Shows information about the selected remote"""

    if ctx.obj["host_config"]["login"]["password"] != "":
        ctx.obj["host_config"]["login"]["password"] = "__OMITTED__"

    log("Remote %s:" % ctx.obj["remote"], ctx.obj["host_config"], pretty=True)


@remote.command(name="list")
@click.pass_context
def list_remotes(ctx):
    """Shows all configured remotes"""

    log("Remotes:", list(ctx.obj["remotes"].keys()), pretty=True)


@remote.command(name="test")
@click.pass_context
def test(ctx):
    """Run and return info command on a remote"""

    shell = ctx.obj["shell"]
    username = ctx.obj["host_config"]["login"]["username"]

    success, result = run_process(
        get_remote_home(username), ["iso", "-nc", "version"], shell=shell
    )
    log(success, "\n", format_result(result), pretty=True)


@remote.command(name="command")
@click.argument("commands", nargs=-1)
@click.pass_context
def command(ctx, commands):
    """Execute a remote command"""

    log("Executing commands %s on remote %s" % (commands, ctx.obj["remote"]))

    shell = ctx.obj["shell"]

    args = ["iso"] + list(commands)

    log(args)

    success, result = run_process(
        get_remote_home(ctx.obj["host_config"]["login"]["username"]), args, shell=shell
    )

    if not success:
        log("Execution error:", format_result(result), pretty=True, lvl=error)
    else:
        log("Success:")
        log(format_result(result))


@remote.command(name="backup")
@click.argument("backup-instance")
@click.option(
    "--fetch",
    "-f",
    help="Fetch remote backup for local storage",
    is_flag=True,
    default=False,
)
@click.option(
    "--target", "-t", help="Fetch to specified target directory", metavar="target"
)
@click.pass_context
def backup(ctx, backup_instance, fetch, target):
    """Backup a remote"""

    log("Backing up %s on remote %s" % (backup_instance, ctx.obj["remote"]))

    shell = ctx.obj["shell"]

    args = [
        "iso",
        "-nc",
        "--clog",
        "10",
        "-i",
        backup_instance,
        "-e",
        "current",
        "environment",
        "archive",
    ]

    log(args)

    success, result = run_process(
        get_remote_home(ctx.obj["host_config"]["login"]["username"]), args, shell=shell
    )

    if not success or b"Archived to" not in result.output:
        log("Execution error:", format_result(result), pretty=True, lvl=error)
    else:
        log("Local backup created")

        if fetch:
            full_path = result.split("'")[1]
            filename = os.path.basename(full_path)

            with shell.open(full_path, "r") as input_file:
                with open(os.path.join(target, filename), "w") as output_file:
                    output = input_file.read()
                    output_file.write(output)

            log("Backup downloaded. Size:", len(output))
