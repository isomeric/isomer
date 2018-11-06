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
from isomer.provisions.base import provisionList

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import click
import os
import shutil
import sys
import networkx

from distutils.dir_util import copy_tree
from subprocess import Popen

from click_didyoumean import DYMGroup

from isomer.tool.etc import NonExistentKey
from isomer.logger import error, warn, debug
from isomer.tool import check_root, log, ask
from isomer.misc.path import get_path, set_instance
from isomer.ui.builder import install_frontend

from git import Repo, exc
from isomer.version import version


@click.group(cls=DYMGroup)
@click.option('--port', help='Specify local HFOS port', default=8055)
@click.pass_context
def install(ctx, port):
    """[GROUP] Install various aspects of HFOS"""

    set_instance(ctx.obj['instance'], "blue")  # Initially start with a blue instance

    log('Configuration:', ctx.obj['config'])
    log('Instance:', ctx.obj['instance'])

    try:
        instance = ctx.obj['config']['instances'][ctx.obj['instance']]
    except NonExistentKey:
        log('Instance unknown, so far.', lvl=warn)

        instance = ctx.obj['config']['defaults']
        log('New instance configuration:', instance)

    environment_name = instance['environment']
    environment = instance['environments'][environment_name]

    environment['port'] = port

    # TODO: Remove sparse&superfluous environment info from context
    ctx.obj['port'] = port

    try:
        repository = Repo('./')
        ctx.obj['repository'] = repository
        log('Repo:', repository)
        environment['version'] = repository.git.describe()
    except exc.InvalidGitRepositoryError:
        log('Not running from a git repository; Using hfos.version', lvl=warn)
        environment['version'] = version

    ctx.obj['environment'] = environment

    ctx.obj['instance_config'] = instance


@install.command(short_help='build and install docs')
@click.option('--clear-target', '--clear', help='Clears target documentation '
                                                'folders', default=False, is_flag=True)
@click.pass_context
def docs(ctx, clear_target):
    """Build and install documentation"""

    install_docs(str(ctx.obj['instance']), clear_target)


def install_docs(instance, clear_target):
    """Builds and installs the complete HFOS documentation."""

    check_root()

    def make_docs():
        """Trigger a Sphinx make command to build the documentation."""
        log("Generating HTML documentation")

        try:
            build = Popen(
                [
                    'make',
                    'html'
                ],
                cwd='docs/'
            )

            build.wait()
        except Exception as e:
            log("Problem during documentation building: ", e, type(e),
                exc=True, lvl=error)
            return False
        return True

    make_docs()

    # If these need changes, make sure they are watertight and don't remove
    # wanted stuff!
    target = os.path.join('/var/lib/hfos', instance, 'frontend/docs')
    source = 'docs/build/html'

    log("Updating documentation directory:", target)

    if not os.path.exists(os.path.join(os.path.curdir, source)):
        log(
            "Documentation not existing yet. Run python setup.py "
            "build_sphinx first.", lvl=error)
        return

    if os.path.exists(target):
        log("Path already exists: " + target)
        if clear_target:
            log("Cleaning up " + target, lvl=warn)
            shutil.rmtree(target)

    log("Copying docs to " + target)
    copy_tree(source, target)
    log("Done: Install Docs")


@install.command(short_help='install provisions')
@click.option('--provision', '-p', help="Specify a provision (default=install "
                                        "all)",
              default=None, metavar='<name>')
@click.option('--clear-existing', '--clear', help='Clears already existing collections (DANGER!)',
              is_flag=True, default=False)
@click.option('--overwrite', '-o', help='Overwrites existing provisions',
              is_flag=True, default=False)
@click.option('--list-provisions', '-l', help='Only list available provisions',
              is_flag=True, default=False)
@click.pass_context
def provisions(ctx, provision, clear_existing, overwrite, list_provisions):
    """Install default provisioning data"""

    install_provisions(ctx, provision, clear_existing, overwrite, list_provisions)


def install_provisions(ctx, provision, clear_provisions=False, overwrite=False, list_provisions=False):
    """Install default provisioning data"""

    log("Installing HFOS default provisions")

    # from hfos.logger import verbosity, events
    # verbosity['console'] = verbosity['global'] = events

    from isomer import database
    database.initialize(ctx.obj['dbhost'], ctx.obj['dbname'])

    from isomer.provisions import build_provision_store

    provision_store = build_provision_store()

    def sort_dependencies(items):
        """Topologically sort the dependency tree"""

        g = networkx.DiGraph()
        log('Sorting dependencies')

        for key, item in items:
            log('key: ', key, 'item:', item, pretty=True, lvl=debug)
            dependencies = item.get('dependencies', [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]

            if key not in g:
                g.add_node(key)

            for link in dependencies:
                g.add_edge(key, link)

        if not networkx.is_directed_acyclic_graph(g):
            log('Cycles in provosioning dependency graph detected!', lvl=error)
            log('Involved provisions:', list(networkx.simple_cycles(g)), lvl=error)

        topology = list(networkx.algorithms.topological_sort(g))
        topology.reverse()

        log(topology, pretty=True)

        return topology

    if list_provisions:
        sort_dependencies(provision_store.items())
        exit()

    def provision_item(item):
        """Provision a single provisioning element"""

        method = item.get('method', provisionList)
        model = item.get('model')
        data = item.get('data')

        method(data, model, overwrite=overwrite, clear=clear_provisions)

    if provision is not None:
        if provision in provision_store:
            log("Provisioning ", provision, pretty=True)
            provision_item(provision_store[provision])
        else:
            log("Unknown provision: ", provision, "\nValid provisions are",
                list(provision_store.keys()),
                lvl=error,
                emitter='MANAGE')
    else:
        for name in sort_dependencies(provision_store.items()):
            log("Provisioning", name, pretty=True)
            provision_item(provision_store[name])

    log("Done: Install Provisions")


@install.command(short_help='install modules')
@click.option('--wip', help="Install Work-In-Progress (alpha/beta-state) modules as well", is_flag=True)
def modules(wip):
    """Install the plugin modules"""

    install_modules(wip)


def install_modules(wip):
    """Install the plugin modules"""

    def install_module(hfos_module):
        """Install a single module via setuptools"""
        try:
            setup = Popen(
                [
                    sys.executable,
                    'setup.py',
                    'develop'
                ],
                cwd='modules/' + hfos_module + "/"
            )

            setup.wait()
        except Exception as e:
            log("Problem during module installation: ", hfos_module, e,
                type(e), exc=True, lvl=error)
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
        'navdata',

        # Now all the rest:
        'alert',
        'automat',
        'busrepeater',
        'calendar',
        'countables',
        'dash',
        # 'dev',
        'enrol',
        'mail',
        'maps',
        'nmea',
        'nodestate',
        'project',
        'webguides',
        'wiki'
    ]

    modules_wip = [
        'calc',
        'camera',
        'chat',
        'comms',
        'contacts',
        'crew',
        'equipment',
        'filemanager',
        'garden',
        'heroic',
        'ldap',
        'library',
        'logbook',
        'protocols',
        'polls',
        'mesh',
        'robot',
        'switchboard',
        'shareables',
    ]

    installables = modules_production

    if wip:
        installables.extend(modules_wip)

    success = []
    failed = []

    for installable in installables:
        log('Installing module ', installable)
        if install_module(installable):
            success.append(installable)
        else:
            failed.append(installable)

    log('Installed modules: ', success)
    if len(failed) > 0:
        log('Failed modules: ', failed)
    log('Done: Install Modules')


@install.command(short_help='build and install frontend')
@click.option('--dev', help="Use frontend development location", default=True, is_flag=True)
@click.option('--rebuild', help="Rebuild frontend before installation", default=False, is_flag=True)
@click.option('--no-install', help="Do not install requirements", default=False, is_flag=True)
@click.option('--build-type', help="Specify frontend build type. Either dist(default) or build", default='dist')
@click.pass_context
def frontend(ctx, dev, rebuild, no_install, build_type):
    """Build and install frontend"""

    install_frontend(instance=ctx.obj['instance'],
                     forcerebuild=rebuild,
                     development=dev,
                     install=not no_install,
                     build_type=build_type)


@install.command('all', short_help='install everything')
@click.option('--clear-all', '--clear', help='Clears already existing cache directories and data', is_flag=True,
              default=False)
@click.pass_context
def install_all(ctx, clear_all):
    """Default-Install everything installable

    \b
    This includes
    * System user (hfos.hfos)
    * Self signed certificate
    * Variable data locations (/var/lib/hfos and /var/cache/hfos)
    * All the official modules in this repository
    * Default module provisioning data
    * Documentation
    * systemd service descriptor

    It does NOT build and install the HTML5 frontend."""

    check_root()

    instance = ctx.obj['instance']
    # dbhost = ctx.obj['dbhost']
    # dbname = ctx.obj['dbname']
    # port = ctx.obj['port']

    # install_system_user()
    # install_cert(selfsigned=True)

    # install_var(instance, clear_target=clear_all, clear_all=clear_all)
    install_modules(wip=False)
    install_provisions(ctx, provision=None, clear_provisions=clear_all)
    install_docs(instance, clear_target=clear_all)

    # install_service(instance, dbhost, dbname, port)
    # install_nginx(instance, dbhost, dbname, port)

    log('Done')


@click.command(short_help='remove stuff in /var')
def uninstall():
    """Uninstall data and resource locations"""

    check_root()

    response = ask("This will delete all data of your HFOS installations! Type"
                    "YES to continue:", default="N", show_hint=False)
    if response == 'YES':
        shutil.rmtree('/var/lib/hfos')
        shutil.rmtree('/var/cache/hfos')


