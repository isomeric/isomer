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

Module: Configuration
=====================

Classic installer tidbits that should probably be moved to places elsewhere,
i.e. isomer.tool.instance and isomer.tool.environment


"""

import click
import os
import shutil
import sys

from distutils.dir_util import copy_tree
from subprocess import Popen

from click_didyoumean import DYMGroup

from isomer.tool.etc import NonExistentKey, instance_template
from isomer.logger import error, warn, debug
from isomer.tool import check_root, log, finish
from isomer.ui.builder import install_frontend
from isomer.provisions.base import provision

from git import Repo, exc
from isomer.version import version


@click.group(
    cls=DYMGroup,
    short_help="Installation helpers"
)
@click.option("--port", help="Specify local Isomer port", default=8055)
@click.pass_context
def install(ctx, port):
    """[GROUP] Install various aspects of Isomer"""

    # TODO: Make this a shortcut for a full instance install

    # set_instance(ctx.obj['instance'], "blue")  # Initially start with a blue instance

    log("Configuration:", ctx.obj["config"])
    log("Instance:", ctx.obj["instance"])

    try:
        instance = ctx.obj["instances"][ctx.obj["instance"]]
    except NonExistentKey:
        log("Instance unknown, so far.", lvl=warn)

        instance = instance_template
        log("New instance configuration:", instance)

    environment_name = instance["environment"]
    environment = instance["environments"][environment_name]

    environment["port"] = port

    # TODO: Remove sparse&superfluous environment info from context
    ctx.obj["port"] = port

    try:
        repository = Repo("./")
        ctx.obj["repository"] = repository
        log("Repo:", repository)
        environment["version"] = repository.git.describe()
    except exc.GitError:
        log("Not running from a git repository or there is a problem with it; "
            "Using isomer.version", lvl=warn)
        environment["version"] = version

    ctx.obj["environment"] = environment


@install.command(short_help="build and install frontend")
@click.option(
    "--dev", help="Use frontend development location", default=False, is_flag=True
)
@click.option(
    "--rebuild",
    help="Rebuild frontend before installation",
    default=False,
    is_flag=True,
)
@click.option(
    "--no-install", help="Do not install requirements", default=False, is_flag=True
)
@click.option(
    "--build-type",
    help="Specify frontend build type. Either dist(default) or build",
    default="dist",
)
@click.pass_context
def frontend(ctx, dev, rebuild, no_install, build_type):
    """Build and install frontend"""

    # TODO: Move this to the environment handling and deprecate it here

    install_frontend(
        force_rebuild=rebuild,
        development=dev,
        install=not no_install,
        build_type=build_type,
    )


@install.command(short_help="build and install docs")
@click.option(
    "--clear-target",
    "--clear",
    help="Clears target documentation " "folders",
    default=False,
    is_flag=True,
)
@click.pass_context
def docs(ctx, clear_target):
    """Build and install documentation"""

    # TODO: Move this to the environment handling and deprecate it here

    install_docs(str(ctx.obj["instance"]), clear_target)
    finish(ctx)


def install_docs(instance, clear_target):
    """Builds and installs the complete Isomer documentation."""

    check_root()

    def make_docs():
        """Trigger a Sphinx make command to build the documentation."""
        log("Generating HTML documentation")

        try:
            build = Popen(["make", "html"], cwd="docs/")

            build.wait()
        except Exception as e:
            log(
                "Problem during documentation building: ",
                e,
                type(e),
                exc=True,
                lvl=error,
            )
            return False
        return True

    make_docs()

    # If these need changes, make sure they are watertight and don't remove
    # wanted stuff!
    target = os.path.join("/var/lib/isomer", instance, "frontend/docs")
    source = "docs/build/html"

    log("Updating documentation directory:", target)

    if not os.path.exists(os.path.join(os.path.curdir, source)):
        log(
            "Documentation not existing yet. Run python setup.py "
            "build_sphinx first.",
            lvl=error,
        )
        return

    if os.path.exists(target):
        log("Path already exists: " + target)
        if clear_target:
            log("Cleaning up " + target, lvl=warn)
            shutil.rmtree(target)

    log("Copying docs to " + target)
    copy_tree(source, target)


@install.command(short_help="install provisions")
@click.option(
    "--package",
    "-p",
    help="Specify a package to provision (default=install all)",
    default=None,
    metavar="<name>",
)
@click.option(
    "--clear-existing",
    "--clear",
    help="Clears already existing collections (DANGER!)",
    is_flag=True,
    default=False,
)
@click.option(
    "--overwrite",
    "-o",
    help="Overwrites existing provisions",
    is_flag=True,
    default=False,
)
@click.option(
    "--list-provisions",
    "-l",
    help="Only list available provisions",
    is_flag=True,
    default=False,
)
@click.pass_context
def provisions(ctx, package, clear_existing, overwrite, list_provisions):
    """Install default provisioning data"""

    # TODO: Move this to the environment handling and deprecate it here

    install_provisions(ctx, package, clear_existing, overwrite, list_provisions)
    finish(ctx)


def install_provisions(
    ctx, package, clear_provisions=False, overwrite=False, list_provisions=False
):
    """Install default provisioning data"""

    log("Installing Isomer default provisions")

    # from isomer.logger import verbosity, events
    # verbosity['console'] = verbosity['global'] = events

    from isomer import database

    log("Instance settings:", ctx.obj, pretty=True, lvl=debug)
    database.initialize(ctx.obj["dbhost"], ctx.obj["dbname"])

    provision(list_provisions, overwrite, clear_provisions, package)


@install.command(short_help="install modules (DEPRECATED)", deprecated=True)
@click.option(
    "--wip",
    help="Install Work-In-Progress (alpha/beta-state) modules as well",
    is_flag=True,
)
def modules(wip):
    """Install the plugin modules"""

    # TODO: Remove altogether, this should be done via instance/environment only

    install_modules(wip)
    log("Done: Install Modules")


def install_modules(wip):
    """Install the plugin modules"""

    def install_module(isomer_module):
        """Install a single module via setuptools"""
        try:
            setup = Popen(
                [sys.executable, "setup.py", "develop"],
                cwd="modules/" + isomer_module + "/",
            )

            setup.wait()
        except Exception as e:
            log(
                "Problem during module installation: ",
                isomer_module,
                e,
                type(e),
                exc=True,
                lvl=error,
            )
            return False
        return True

    # TODO: Sort module dependencies via topological sort or let pip do this in future.
    # # To get the module dependencies:
    # packages = {}
    # for provision_entrypoint in iter_entry_points(group='isomer.provisions',
    #                                               name=None):
    #     log("Found packages: ", provision_entrypoint.dist.project_name, lvl=warn)
    #
    #     _package_name = provision_entrypoint.dist.project_name
    #     _package = pkg_resources.working_set.by_key[_package_name]
    #
    #     print([str(r) for r in _package.requires()])  # retrieve deps from setup.py

    modules_production = [
        # TODO: Poor man's dependency management, as long as the modules are
        # installed from local sources and they're not available on pypi,
        # which would handle real dependency management for us:
        "navdata",
        # Now all the rest:
        "alert",
        "automat",
        "busrepeater",
        "calendar",
        "countables",
        "dash",
        # 'dev',
        "enrol",
        "mail",
        "maps",
        "nmea",
        "nodestate",
        "project",
        "webguides",
        "wiki",
    ]

    modules_wip = [
        "calc",
        "camera",
        "chat",
        "comms",
        "contacts",
        "crew",
        "equipment",
        "filemanager",
        "garden",
        "heroic",
        "ldap",
        "library",
        "logbook",
        "protocols",
        "polls",
        "mesh",
        "robot",
        "switchboard",
        "shareables",
    ]

    installables = modules_production

    if wip:
        installables.extend(modules_wip)

    success = []
    failed = []

    for installable in installables:
        log("Installing module ", installable)
        if install_module(installable):
            success.append(installable)
        else:
            failed.append(installable)

    log("Installed modules: ", success)
    if len(failed) > 0:
        log("Failed modules: ", failed)
