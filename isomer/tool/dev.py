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

Module: Dev
===========

A collection of developer support tools.

"""

import time
import pkg_resources
import click
import os
import shutil

from pprint import pprint
from click_didyoumean import DYMGroup
from collections import OrderedDict, namedtuple
from operator import attrgetter

from isomer.tool import log, ask, debug, verbose, warn
from isomer.misc.std import std_table
from isomer.tool.templates import write_template_file
from isomer.error import abort
from isomer.ui.store.inventory import populate_store, get_inventory

paths = [
    "isomer",
    "isomer/{plugin_name}",
    "isomer-frontend/{plugin_name}/scripts/controllers",
    "isomer-frontend/{plugin_name}/views",
]

templates = {
    "setup_file": ("setup.py.template", "setup.py"),
    "package_file": ("package.json.template", "package.json"),
    "component": ("component.py.template", "isomer/{plugin_name}/{plugin_name}.py"),
    "module_init": ("init.py.template", "isomer/__init__.py"),
    "package_init": ("init.py.template", "isomer/{plugin_name}/__init__.py"),
    "schemata": ("schemata.py.template", "isomer/{plugin_name}/schemata.py"),
    "controller": (
        "controller.js.template",
        "isomer-frontend/{plugin_name}/scripts/controllers/{" "plugin_name}.js",
    ),
    "view": (
        "view.html.template",
        "isomer-frontend/{plugin_name}/views/{plugin_name}.html",
    ),
}

questions = OrderedDict(
    {
        "plugin_name": "plugin",
        "author_name": u"author",
        "author_email": u"author@domain.tld",
        "description": u"Description",
        "long_description": u"Very long description, use \\n to get multilines.",
        "version": "0.0.1",
        "github_url": "isomeric/example",
        "license": "GPLv3",
        "keywords": "Isomer example plugin",
    }
)

info_header = """The manage command guides you through setting up a new isomer
package.
It provides basic setup. If you need dependencies or have other special
needs, edit the resulting files by hand.

You can press Ctrl-C any time to cancel this process.

See iso create-module --help for more details.
"""


def _augment_info(info):
    """Fill out the template information"""

    info["description_header"] = "=" * len(info["description"])
    info["component_name"] = info["plugin_name"].capitalize()
    info["year"] = time.localtime().tm_year
    info["license_longtext"] = ""

    info["keyword_list"] = u""
    for keyword in info["keywords"].split(" "):
        print(keyword)
        info["keyword_list"] += u"'" + str(keyword) + u"', "
    print(info["keyword_list"])
    if len(info["keyword_list"]) > 0:
        # strip last comma
        info["keyword_list"] = info["keyword_list"][:-2]

    return info


def _construct_module(info, target):
    """Build a module from templates and user supplied information"""

    for path in paths:
        real_path = os.path.abspath(os.path.join(target, path.format(**info)))
        log("Making directory '%s'" % real_path)
        os.makedirs(real_path)

    # pprint(info)
    for item in templates.values():
        source = os.path.join("dev/templates", item[0])
        filename = os.path.abspath(os.path.join(target, item[1].format(**info)))
        log("Creating file from template '%s'" % filename, emitter="MANAGE")
        write_template_file(source, filename, info)


def _ask_questionnaire():
    """Asks questions to fill out a Isomer plugin template"""

    answers = {}
    print(info_header)
    pprint(questions.items())

    for question, default in questions.items():
        response = ask(question, default, str(type(default)), show_hint=True)
        if type(default) == bytes and type(response) != str:
            response = response.decode("utf-8")
        answers[question] = response

    return answers


@click.group(cls=DYMGroup)
def dev():
    """[GROUP] Developer support operations"""


@dev.command(short_help="create starterkit module")
@click.option(
    "--clear-target",
    "--clear",
    help="Clears already existing target",
    default=False,
    is_flag=True,
)
@click.option(
    "--target",
    help="Create module in the given folder (uses ./ if omitted)",
    default=".",
    metavar="<folder>",
)
def create_module(clear_target, target):
    """Creates a new template Isomer plugin module"""

    if os.path.exists(target):
        if clear_target:
            shutil.rmtree(target)
        else:
            log("Target exists! Use --clear to delete it first.", emitter="MANAGE")
            abort(2)

    done = False
    info = None

    while not done:
        info = _ask_questionnaire()
        pprint(info)
        done = ask("Is the above correct", default="y", data_type="bool")

    augmented_info = _augment_info(info)

    log("Constructing module %(plugin_name)s" % info)
    _construct_module(augmented_info, target)


@dev.command(short_help="List setuptools installed component information")
@click.option(
    "--base",
    "-b",
    is_flag=True,
    default=False,
    help="Also list isomer-base (integrated) modules",
)
@click.option(
    "--sails",
    "-s",
    is_flag=True,
    default=False,
    help="Also list isomer-sails (integrated) modules",
)
@click.option(
    "--schemata",
    is_flag=True,
    default=False,
    help="Also list registered schemata"
)
@click.option(
    "--management",
    is_flag=True,
    default=False,
    help="Also list registered management commands"
)
@click.option(
    "--provisions",
    is_flag=True,
    default=False,
    help="Also list registered provisions"
)
@click.option(
    "--frontend-only",
    "-f",
    is_flag=True,
    default=False,
    help="Only list modules with a frontend",
)
@click.option(
    "--frontend-list",
    "-l",
    is_flag=True,
    default=False,
    help="List files in frontend per module",
)
@click.option(
    "--directory", "-d", is_flag=True, default=False, help="Show directory of module"
)
@click.option(
    "--sort-key",
    "-k",
    default="package",
    type=click.Choice(
        ["name", "package", "classname", "location", "frontend", "group"]),
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="List all registered entrypoints"
)
@click.option(
    "--filter",
    "-f",
    default="",
    type=str,
    help="Filter table by string"
)
@click.option("--long", is_flag=True, default=False, help="Show full table")
def entrypoints(base, sails, schemata, management, provisions, frontend_only,
                frontend_list, directory, sort_key, all, filter, long):
    """Display list of entrypoints and diagnose module loading problems."""

    log("Showing entrypoints:")

    full_component = namedtuple(
        "Component", ["name", "package", "classname", "location", "frontend", "group"]
    )
    component = namedtuple("Component", ["name", "package", "frontend", "group"])
    results = []

    from pkg_resources import iter_entry_points

    entry_points = {
        "components": iter_entry_points(group="isomer.components", name=None)
    }

    if all:
        sails = base = schemata = management = provisions = True

    if sails:
        entry_points["sails"] = iter_entry_points(group="isomer.sails", name=None)
    if base:
        entry_points["base"] = iter_entry_points(group="isomer.base", name=None)
    if schemata:
        entry_points["schemata"] = iter_entry_points(group="isomer.schemata", name=None)
    if management:
        entry_points["management"] = iter_entry_points(group="isomer.management",
                                                       name=None)
    if provisions:
        entry_points["provisions"] = iter_entry_points(group="isomer.provisions",
                                                       name=None)

    log("Entrypoints:", entry_points, pretty=True, lvl=verbose)
    try:
        for key, iterator in entry_points.items():
            for entry_point in iterator:
                log("Entrypoint Group:", key, entry_point, pretty=True, lvl=debug)

                try:
                    name = entry_point.name
                    package = entry_point.dist.project_name
                    log("Package:", package, pretty=True, lvl=debug)
                    location = entry_point.dist.location
                    try:
                        loaded = entry_point.load()
                    except pkg_resources.DistributionNotFound as e:
                        log(
                            "Required distribution not found:",
                            e,
                            pretty=True,
                            exc=True,
                            lvl=warn,
                        )
                        continue

                    log(
                        "Entry point: ",
                        entry_point,
                        name,
                        entry_point.resolve(),
                        location,
                        lvl=debug,
                    )

                    log("Loaded: ", loaded, lvl=debug)

                    try:
                        pkg = pkg_resources.Requirement.parse(package)
                        frontend = pkg_resources.resource_listdir(pkg, "frontend")
                        log("Frontend resources found:", frontend, lvl=debug)
                    except Exception as e:
                        log(
                            "Exception during frontend resource lookup:",
                            e,
                            lvl=debug,
                            exc=True,
                        )
                        frontend = None

                    if frontend not in (None, []):
                        log("Contains frontend parts", lvl=debug)
                        if not frontend_list:
                            frontend = "[X]"
                    else:
                        frontend = "[ ]"

                    if filter != "":
                        if filter not in name and filter not in package and filter not in location:
                            continue

                    if long:
                        if key in ("schemata", "provisions"):
                            classname = "[SCHEMA]"
                        else:
                            classname = repr(loaded).lstrip("<class '").rstrip("'>")

                        result = full_component(
                            frontend=frontend,
                            name=name,
                            package=package,
                            classname=classname,
                            location=location if directory else "use -d",
                            group=key,
                        )
                    else:
                        result = component(
                            frontend=frontend, name=name, package=package, group=key
                        )

                    if not frontend_only or frontend:
                        results.append(result)
                except ImportError as e:
                    log("Exception while iterating entrypoints:", e, type(e), lvl=warn,
                        exc=True)
    except ModuleNotFoundError as e:
        log("Module could not be loaded:", e, exc=True)

    results = sorted(results, key=attrgetter(sort_key))

    table = std_table(results)
    log("\n%s" % table)


@dev.command(short_help="Grab and show software store inventory")
@click.option(
    "--source",
    help="Specify a different source than official Isomer",
    default="https://store.isomer.eu/simple",
    metavar="<url>",
)
def store_inventory(source):
    """List available pacakages"""

    store = populate_store(source)

    log(store, pretty=True)


@dev.command(short_help="Show local inventory")
@click.pass_context
def local_inventory(ctx):
    """List installed pacakages"""

    inventory = get_inventory(ctx)

    log(inventory, pretty=True)
