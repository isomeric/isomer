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

Module: Environment
===================

Environment management functionality.

    environment clear
    environment archive
    environment install-frontend
    environment install-module
    environment install-provisions
    environment install

"""
import pymongo

import grp
import os
import pwd
import shutil
import sys
import tarfile
import click

from tempfile import mkdtemp
from click_didyoumean import DYMGroup
from git import Repo, exc

from isomer.scm_version import version
from isomer.database.backup import dump, load
from isomer.logger import error, verbose, warn, critical, debug, hilight
from isomer.misc import std_uuid, std_now
from isomer.misc.path import (
    set_instance,
    get_path,
    get_etc_path,
    locations,
    get_log_path,
    get_etc_instance_path,
)
from isomer.tool import (
    log,
    finish,
    run_process,
    format_result,
    get_isomer,
    _get_configuration,
    get_next_environment,
)
from isomer.tool.database import delete_database
from isomer.tool.defaults import source_url
from isomer.error import abort, EXIT_INVALID_SOURCE
from isomer.tool.etc import write_instance, environment_template


@click.group(cls=DYMGroup)
@click.pass_context
def environment(ctx):
    """[GROUP] Various aspects of Isomer environment handling"""

    _get_configuration(ctx)


def _check_environment(ctx, env=None):
    """General fitness tests of the built environment"""
    # TODO: Implement environment testing

    if env is None:
        env = get_next_environment(ctx)
    log("Would now health check the environment '%s' (Not implemented, yet)" % env)
    return True


@environment.command(name="clear", short_help="Clear an environment")
@click.option("--force", "-f", is_flag=True, default=False)
@click.option("--no-archive", "-n", is_flag=True, default=False)
@click.pass_context
def clear_environment(ctx, force, no_archive):
    """Clear the non-active environment"""

    _clear_environment(ctx, force, no_archive=no_archive)


def _clear_environment(ctx, force=False, clear_env=None, clear=False, no_archive=False):
    """Tests an environment for usage, then clears it"""

    instance_name = ctx.obj["instance"]

    if clear_env is None:
        next_environment = get_next_environment(ctx)
    else:
        next_environment = clear_env

    log("Clearing environment:", next_environment)
    set_instance(instance_name, next_environment)

    # log('Testing', environment, 'for usage')

    env = ctx.obj["instance_configuration"]["environments"][next_environment]

    if not no_archive:
        if not (_archive(ctx, force) or force):
            log("Archival failed, stopping.")
            abort(5000)

    log("Clearing env:", env, lvl=debug)

    for item in locations:
        path = get_path(item, "")
        log("Clearing [%s]: %s" % (item, path), lvl=debug)
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            log("Path not found:", path, lvl=debug)
        except PermissionError:
            log("No permission to clear environment", lvl=error)
            return False

    if not clear:
        _create_folders(ctx)

    try:
        delete_database(
            ctx.obj["dbhost"], "%s_%s" % (instance_name, next_environment), force=True
        )
    except pymongo.errors.ServerSelectionTimeoutError:
        log("No database available")
    except Exception as e:
        log("Could not delete database:", e, lvl=warn, exc=True)

    ctx.obj["instance_configuration"]["environments"][
        next_environment
    ] = environment_template
    write_instance(ctx.obj["instance_configuration"])
    return True


def _create_folders(ctx):
    """Generate required folders for an instance"""

    log("Generating instance directories", emitter="MANAGE")

    instance_configuration = ctx.obj["instance_configuration"]

    try:
        uid = pwd.getpwnam(instance_configuration["user"]).pw_uid
        gid = grp.getgrnam(instance_configuration["group"]).gr_gid
    except KeyError:
        log("User account for instance not found!", lvl=warn)
        uid = gid = None

    logfile = os.path.join(get_log_path(), "isomer." + ctx.obj["instance"] + ".log")

    for item in locations:
        path = get_path(item, "", ensure=True)

        log("Created path: " + path, lvl=debug)
        if os.geteuid() == 0 and uid is not None:
            os.chown(path, uid, gid)
        else:
            log("No root access - could not change ownership:", path, lvl=warn)

    module_path = get_path("lib", "modules", ensure=True)
    if os.geteuid() == 0 and uid is not None:
        os.chown(module_path, uid, gid)
    else:
        log("No root access - could not change ownership:", module_path, lvl=warn)

    log("Module storage created:", module_path, lvl=debug)

    if not os.path.exists(logfile):
        open(logfile, "w").close()

    if os.geteuid() == 0 and uid is not None:
        os.chown(logfile, uid, gid)
    else:
        log("No root access - could not change ownership", lvl=warn)

    finish(ctx)


@environment.command(short_help="Archive an environment")
@click.option("--force", "-f", is_flag=True, default=False)
@click.option(
    "--dynamic",
    "-d",
    is_flag=True,
    default=False,
    help="Archive only dynamic data: database, configuration",
)
@click.pass_context
def archive(ctx, force, dynamic):
    """Archive the specified or non-active environment"""

    result = _archive(ctx, force, dynamic)
    if result:
        log("Archived to '%s'" % result)
        finish(ctx)
    else:
        log("Could not archive.", lvl=error)
        abort(50060)


def _archive(ctx, force=False, dynamic=False):
    instance_configuration = ctx.obj["instance_configuration"]

    next_environment = get_next_environment(ctx)

    env = instance_configuration["environments"][next_environment]

    log(instance_configuration, next_environment, pretty=True)
    log(env["installed"], env["tested"])
    if (not env["installed"] or not env["tested"]) and not force:
        log("Environment has not been installed - not archiving.", lvl=warn)
        return False

    log("Archiving environment:", next_environment)
    set_instance(ctx.obj["instance"], next_environment)

    timestamp = std_now().replace(":", "-").replace(".", "-")

    temp_path = mkdtemp(prefix="isomer_backup")

    log("Archiving database")
    if not dump(
        instance_configuration["database_host"],
        instance_configuration["database_port"],
        env["database"],
        os.path.join(temp_path, "db_" + timestamp + ".json"),
    ):
        if not force:
            log("Could not archive database.")
            return False

    archive_filename = os.path.join(
        "/var/backups/isomer/",
        "%s_%s_%s.tgz" % (ctx.obj["instance"], next_environment, timestamp),
    )

    try:
        shutil.copy(
            os.path.join(get_etc_instance_path(), ctx.obj["instance"] + ".conf"),
            temp_path,
        )

        with tarfile.open(archive_filename, "w:gz") as f:
            if not dynamic:
                for item in locations:
                    path = get_path(item, "")
                    log("Archiving [%s]: %s" % (item, path))
                    f.add(path)
            f.add(temp_path, "db_etc")
    except (PermissionError, FileNotFoundError) as e:
        log("Could not archive environment:", e, lvl=error)
        if not force:
            return False
    finally:
        log("Clearing temporary backup target")
        shutil.rmtree(temp_path)

    ctx.obj["instance_configuration"]["environments"]["archive"][timestamp] = env

    log(ctx.obj["instance_configuration"])

    return archive_filename


@environment.command(short_help="Install frontend")
@click.pass_context
def install_frontend(ctx):
    """Install frontend into an environment"""

    next_environment = get_next_environment(ctx)

    set_instance(ctx.obj["instance"], next_environment)
    _install_frontend(ctx)
    finish(ctx)


def _install_frontend(ctx):
    """Install and build the frontend"""

    env = get_next_environment(ctx)
    env_path = get_path("lib", "")

    instance_configuration = ctx.obj["instance_configuration"]

    user = instance_configuration["user"]

    log("Building frontend")

    success, result = run_process(
        os.path.join(env_path, "repository"),
        [
            os.path.join(env_path, "venv", "bin", "python3"),
            "./iso",
            "-nc",
            "--config-dir",
            get_etc_path(),
            "-i",
            instance_configuration["name"],
            "-e",
            env,
            "install",
            "frontend",
            "--rebuild",
        ],
        sudo=user,
    )
    if not success:
        log(format_result(result), lvl=error)
        return False

    return True


@environment.command(
    "install-env-modules", short_help="Install a module into an environment"
)
@click.option(
    "--source", "-s", default="git", type=click.Choice(["link", "copy", "git"])
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Force installation (overwrites old modules)",
)
@click.argument("urls", nargs=-1)
@click.pass_context
def install_environment_modules(ctx, source, force, urls):
    """Add and install a module only to a single environment

    Note: This does not modify the instance configuration, so this will not
    be permanent during upgrades etc.
    """

    instance_name = ctx.obj["instance"]
    instance_configuration = ctx.obj["instances"][instance_name]

    next_environment = get_next_environment(ctx)
    user = instance_configuration["user"]
    installed = instance_configuration["environments"][next_environment]["installed"]

    if not installed:
        log("Please install the '%s' environment first." % next_environment, lvl=error)
        abort(50000)

    set_instance(instance_name, next_environment)

    for url in urls:
        result = _install_module(source, url, force, user)

        if result is False:
            log("Installation failed!", lvl=error)
            abort(50000)

        package_name, package_version = result

        descriptor = {"version": package_version, "source": source, "url": url}
        instance_configuration["environments"][next_environment]["modules"][
            package_name
        ] = descriptor

    write_instance(instance_configuration)

    finish(ctx)


def _install_module(source, url, force=False, user=None):
    """Actually installs a module into an environment"""

    def get_module_info(directory):
        log("Getting name")
        success, result = run_process(
            directory, ["python3", "setup.py", "--name"], sudo=user
        )
        if not success:
            log(format_result(result), pretty=True, lvl=error)
            return False

        package_name = str(result.output, encoding="utf8").rstrip("\n")

        log("Getting version")
        success, result = run_process(
            directory, ["python3", "setup.py", "--version"], sudo=user
        )
        if not success:
            log(format_result(result), pretty=True, lvl=error)
            return False

        package_version = str(result.output, encoding="utf8").rstrip("\n")

        log("Package name:", package_name, "version:", package_version)
        return package_name, package_version

    if source == "develop":
        log("Installing module for development")
        success, output = run_process(
            url,
            [
                os.path.join(get_path("lib", "venv"), "bin", "python3"),
                "setup.py",
                "develop",
            ],
            sudo=user,
        )
        if not success:
            log(output, lvl=verbose)
            return False
        else:
            return get_module_info(url)

    module_path = get_path("lib", "modules", ensure=True)

    if source not in ("git", "link", "copy"):
        log("Only installing from github or local is currently supported", lvl=error)
        abort(EXIT_INVALID_SOURCE)

    uuid = std_uuid()
    temporary_path = os.path.join(module_path, "%s" % uuid)

    log("Installing module: %s [%s]" % (url, source))

    if source == "git":
        log("Cloning repository from", url)
        success, output = run_process(
            module_path, ["git", "clone", url, temporary_path], sudo=user
        )
        if not success:
            log("Error:", output, lvl=error)
    elif source == "link":
        log("Linking repository from", url)
        success, output = run_process(
            module_path, ["ln", "-s", url, temporary_path], sudo=user
        )
        if not success:
            log("Error:", output, lvl=error)
    elif source == "copy":
        log("Copying repository from", url)
        success, output = run_process(
            module_path, ["cp", "-a", url, temporary_path], sudo=user
        )
        if not success:
            log("Error:", output, lvl=error)

    module_info = get_module_info(temporary_path)
    if module_info is False:
        log("Could not get name and version information from module.", lvl=error)
        return False

    package_name, package_version = module_info

    final_path = os.path.join(module_path, package_name)

    if os.path.exists(final_path):
        log("Module exists.", lvl=warn)
        if force:
            log("Removing previous version.")
            success, result = run_process(
                module_path, ["rm", "-rf", final_path], sudo=user
            )
            if not success:
                log("Could not remove previous version!", lvl=error)
                abort(50000)
        else:
            log("Not overwriting previous version without --force", lvl=error)
            abort(50000)

    log("Renaming to", final_path)
    os.rename(temporary_path, final_path)

    log("Installing module")
    success, output = run_process(
        final_path,
        [
            os.path.join(get_path("lib", "venv"), "bin", "python3"),
            "setup.py",
            "develop",
        ],
        sudo=user,
    )
    if not success:
        log(output, lvl=verbose)
        return False
    else:
        return package_name, package_version


@environment.command()
@click.pass_context
def install_modules(ctx):
    """Installs all instance configured modules

    To configure (and install) modules for an instance, use

        iso instance install-modules -s <SOURCE> [URLS]

    To immediately install them, add --install
    """

    _install_modules(ctx)

    finish(ctx)


def _install_modules(ctx):
    """Internal function to install modules"""

    env = get_next_environment(ctx)
    log("Installing modules into", env, pretty=True)

    instance_configuration = ctx.obj["instance_configuration"]

    modules = instance_configuration["modules"]
    user = instance_configuration["user"]

    if len(modules) == 0:
        log("No modules defined for instance")
        return True

    for module in modules:
        log("Installing:", module, pretty=True)
        result = _install_module(module[0], module[1], user=user)
        if result is False:
            log("Installation of module failed!", lvl=warn)
        else:
            module_name, module_version = result
            descriptor = {"name": module_name, "source": module[0], "url": module[1]}
            instance_configuration["environments"][env]["modules"][
                module_name
            ] = descriptor

    write_instance(instance_configuration)
    return True


@environment.command(short_help="Install provisions and/or a database backup")
@click.option(
    "--import-file", "--import", default=None, help="Import the specified backup"
)
@click.option("--skip-provisions", is_flag=True, default=False)
@click.pass_context
def install_provisions(ctx, import_file, skip_provisions):
    """Install provisions and/or a database dump"""
    _install_provisions(ctx, import_file, skip_provisions)

    finish(ctx)


def _install_provisions(ctx, import_file=None, skip_provisions=False):
    """Load provisions into database"""

    instance_configuration = ctx.obj["instance_configuration"]
    env = get_next_environment(ctx)
    env_path = get_path("lib", "")

    log("Installing provisioning data")

    if not skip_provisions:
        success, result = run_process(
            os.path.join(env_path, "repository"),
            [
                os.path.join(env_path, "venv", "bin", "python3"),
                "./iso",
                "-nc",
                "--flog",
                "5",
                "--config-dir",
                get_etc_path(),
                "-i",
                instance_configuration["name"],
                "-e",
                env,
                "install",
                "provisions",
            ],  # Note: no sudo necessary as long as we do not enforce authentication on databases
        )
        if not success:
            log("Could not provision data:", lvl=error)
            log(format_result(result), lvl=error)
            return False

    if import_file is not None:
        log("Importing backup")
        log(ctx.obj, pretty=True)
        host, port = ctx.obj["dbhost"].split(":")
        load(host, int(port), ctx.obj["dbname"], import_file)

    return True


def _migrate(ctx):
    """Migrate all data objects"""
    # TODO: Implement migration
    log("Would now migrate (Not implemented, yet)")
    return True


@environment.command(name="install", short_help="Install the other environment")
@click.option("--force", "-f", is_flag=True, default=False)
@click.option(
    "--source", "-s", default="git", type=click.Choice(["link", "copy", "git"])
)
@click.option("--url", "-u", default=None)
@click.option(
    "--import-file", "--import", default=None, help="Import the specified backup"
)
@click.option(
    "--no-sudo",
    is_flag=True,
    default=False,
    help="Do not use sudo to install (Mostly for tests)",
)
@click.option("--skip-modules", is_flag=True, default=False)
@click.option("--skip-data", is_flag=True, default=False)
@click.option("--skip-frontend", is_flag=True, default=False)
@click.option("--skip-test", is_flag=True, default=False)
@click.option("--skip-provisions", is_flag=True, default=False)
@click.pass_context
def install_environment(ctx, **kwargs):
    """Install an environment"""

    _install_environment(ctx, **kwargs)

    finish(ctx)


def _install_environment(
    ctx,
    source,
    url,
    import_file,
    no_sudo,
    force,
    skip_modules,
    skip_data,
    skip_frontend,
    skip_test,
    skip_provisions
):
    """Internal function to perform environment installation"""

    if url is None:
        url = source_url

    instance_name = ctx.obj["instance"]
    instance_configuration = ctx.obj["instance_configuration"]

    next_environment = get_next_environment(ctx)

    set_instance(instance_name, next_environment)

    env = instance_configuration["environments"][next_environment]

    env["database"] = instance_name + "_" + next_environment

    env_path = get_path("lib", "")

    user = instance_configuration["user"]

    if no_sudo:
        user = None

    log(
        "Installing new other environment for %s on %s from %s in %s"
        % (instance_name, next_environment, source, env_path)
    )

    try:
        result = get_isomer(source, url, env_path, sudo=user)
        if result is False:
            log("Getting Isomer failed", lvl=critical)
            abort(50011)
    except FileExistsError:
        if not force:
            log(
                "Isomer already present, please safely clear or "
                "inspect the environment before continuing! Use --force to ignore.",
                lvl=warn,
            )
            abort(50012)
        else:
            log("Isomer already present, forcing through anyway.")

    try:
        repository = Repo(os.path.join(env_path, "repository"))

        log("Repo:", repository, lvl=debug)
        env["version"] = repository.git.describe()
    except (exc.InvalidGitRepositoryError, exc.NoSuchPathError, exc.GitCommandError):
        env["version"] = version
        log(
            "Not running from a git repository; Using isomer.version:",
            version,
            lvl=warn,
        )

    instance_configuration["environments"][next_environment] = env
    write_instance(instance_configuration)

    log("Creating virtual environment")
    success, result = run_process(
        env_path,
        ["virtualenv", "-p", "/usr/bin/python3", "--system-site-packages", "venv"],
        sudo=user,
    )
    if not success:
        log(format_result(result), lvl=error)

    try:
        if _install_backend(ctx):
            log("Backend installed")
            env["installed"] = True
        if not skip_modules and _install_modules(ctx):
            log("Modules installed")
            # env['installed_modules'] = True
        if not skip_provisions and _install_provisions(ctx, import_file=import_file):
            log("Provisions installed")
            env["provisioned"] = True
        if not skip_data and _migrate(ctx):
            log("Data migrated")
            env["migrated"] = True
        if not skip_frontend and _install_frontend(ctx):
            log("Frontend installed")
            env["frontend"] = True
        if not skip_test and _check_environment(ctx):
            log("Environment tested")
            env["tested"] = True
    except Exception:
        log("Error during installation:", exc=True, lvl=critical)

    log("Environment status now:", env)

    ctx.obj["instance_configuration"]["environments"][next_environment] = env

    write_instance(ctx.obj["instance_configuration"])


def _install_backend(ctx):
    """Installs the backend into an environment"""

    instance_name = ctx.obj["instance"]

    set_instance(instance_name, get_next_environment(ctx))

    env_path = get_path("lib", "")
    user = ctx.obj["instance_configuration"]["user"]

    log("Installing backend")
    success, result = run_process(
        os.path.join(env_path, "repository"),
        [os.path.join(env_path, "venv", "bin", "python3"), "setup.py", "develop"],
        sudo=user,
    )
    if not success:
        output = str(result)

        if "was unable to detect version" in output:
            log(
                "Installing from dirty repository. This might result in dependency version problems!",
                lvl=hilight,
            )
        else:
            log(
                "Something unexpected happened during backend installation:\n",
                result,
                lvl=hilight,
            )

        # TODO: Another fault might be an unclean package path. But i forgot the log message to check for.
        # log('This might be a problem due to unclean installations of Python libraries. Please check your path.')

    log("Installing requirements")
    success, result = run_process(
        os.path.join(env_path, "repository"),
        [
            os.path.join(env_path, "venv", "bin", "pip3"),
            "install",
            "-r",
            "requirements.txt",
        ],
        sudo=user,
    )
    if not success:
        log(format_result(result), lvl=error)

    return True
