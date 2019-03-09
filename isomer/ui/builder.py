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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""
Frontend building process
"""

import os
import pkg_resources
from glob import glob
from shutil import copy

from isomer.logger import isolog, debug, verbose, warn, error, critical, hilight
from isomer.misc.path import get_path

try:
    from subprocess import Popen
except ImportError:
    # noinspection PyUnresolvedReferences,PyUnresolvedReferences
    from subprocess32 import Popen  # NOQA


def log(*args, **kwargs):
    """Log as builder emitter"""
    kwargs.update({'emitter': 'BUILDER', 'frame_ref': 2})
    isolog(*args, **kwargs)


def copy_directory_tree(root_src_dir, root_dst_dir, hardlink=True):
    """Copies a whole directory tree"""

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            try:
                if os.path.exists(dst_file):
                    if hardlink:
                        log('Removing frontend link:', dst_file,
                            lvl=verbose)
                        os.remove(dst_file)
                    else:
                        log('Overwriting frontend file:', dst_file,
                            lvl=verbose)
                else:
                    log('Target not existing:', dst_file, lvl=verbose)
            except PermissionError as e:
                log('No permission to remove target:', e, lvl=error)

            try:
                if hardlink:
                    log('Hardlinking ', src_file, dst_dir, lvl=verbose)
                    os.link(src_file, dst_file)
                else:
                    log('Copying ', src_file, dst_dir, lvl=verbose)
                    copy(src_file, dst_dir)
            except PermissionError as e:
                log(
                    " No permission to create target %s for frontend:" % ('link' if hardlink else 'copy'),
                    dst_dir, e, lvl=error)
            except Exception as e:
                log("Error during", 'link' if hardlink else 'copy',
                    "creation:", type(e), e,
                    lvl=error)

            log('Done linking', root_dst_dir,
                lvl=verbose)


def copy_resource_tree(package, source, target):
    """Copies a whole resource tree"""

    pkg = pkg_resources.Requirement.parse(package)

    log('Copying component frontend tree for %s to %s (%s)' % (package, target, source), lvl=debug)

    if not os.path.exists(target):
        os.mkdir(target)

    for item in pkg_resources.resource_listdir(pkg, source):
        log('Handling resource item:', item, lvl=verbose)

        if item in ('__pycache__', '__init__.py'):
            continue

        target_name = os.path.join(target, source.split('frontend')[1].lstrip('/'), item)
        log('Would copy to:', target_name, lvl=verbose)

        if pkg_resources.resource_isdir(pkg, source + '/' + item):
            log('Creating subdirectory:', target_name, lvl=debug)
            try:
                os.mkdir(target_name)
            except FileExistsError:
                log('Subdirectory already exists, ignoring', lvl=debug)

            log('Recursing resource subdirectory:', source + '/' + item, lvl=debug)
            copy_resource_tree(package, source + '/' + item, target)
        else:
            log('Copying resource file:', source + '/' + item, lvl=debug)
            with open(target_name, 'w') as f:
                f.write(pkg_resources.resource_string(pkg, source + '/' + item).decode('utf-8'))


def install_frontend(instance='default', forcereload=False, forcerebuild=False,
                     forcecopy=True, install=True, development=False, build_type='dist'):
    """Builds and installs the frontend"""

    log("Updating frontend components")
    components = {}

    if development:
        frontend_root = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../frontend")
        frontend_target = get_path('lib', 'frontend-dev')
        if not os.path.exists(frontend_target):
            try:
                os.makedirs(frontend_target)
            except PermissionError:
                log('Cannot create development frontend target! Check permissions on', frontend_target)
                return
    else:
        frontend_root = get_path('lib', 'repository/frontend')
        frontend_target = get_path('lib', 'frontend')

    if install:
        cmdline = ["npm", "install"]

        log("Running", cmdline, lvl=verbose)
        npminstall = Popen(cmdline, cwd=frontend_root)

        out, err = npminstall.communicate()

        npminstall.wait()

        log("Frontend dependency installing done: ", out,
            err, lvl=debug)

    try:
        from pkg_resources import iter_entry_points

        entry_point_tuple = (
            iter_entry_points(group='isomer.base', name=None),
            iter_entry_points(group='isomer.sails', name=None),
            iter_entry_points(group='isomer.components', name=None)
        )

        for iterator in entry_point_tuple:
            for entry_point in iterator:
                try:
                    name = entry_point.name
                    package = entry_point.dist.project_name
                    location = entry_point.dist.location
                    loaded = entry_point.load()

                    if package == 'isomer':
                        continue

                    log('Package:', package, lvl=debug)

                    log("Entry point: ", entry_point, name, entry_point.resolve().__module__, lvl=debug)
                    component_name = entry_point.resolve().__module__.split('.')[1]

                    log("Loaded: ", loaded, lvl=verbose)
                    component = {
                        'location': location,
                        'version': str(entry_point.dist.parsed_version),
                        'description': loaded.__doc__,
                        'package': package
                    }

                    try:
                        pkg = pkg_resources.Requirement.parse(package)
                        log('Checking component data resources', lvl=debug)
                        resources = pkg_resources.resource_listdir(pkg, 'frontend')
                        if len(resources) > 0:
                            component['frontend'] = resources
                            component['method'] = 'resources'
                    except ModuleNotFoundError:
                        frontend = os.path.join(location, 'frontend')
                        log("Checking component data folders ", frontend, lvl=verbose)
                        if os.path.isdir(frontend) and frontend != frontend_root:
                            component['frontend'] = frontend
                            component['method'] = 'folder'

                    if 'frontend' not in component:
                        log("Component without frontend directory:", component, lvl=debug)
                    else:
                        components[component_name] = component

                except Exception as e:
                    log("Could not inspect entrypoint: ", e,
                        type(e), entry_point, iterator, lvl=error,
                        exc=True)

        # frontends = iter_entry_points(group='isomer.frontend', name=None)
        # for entrypoint in frontends:
        #     name = entrypoint.name
        #     location = entrypoint.dist.location
        #
        #     log('Frontend entrypoint:', name, location, entrypoint, lvl=hilight)

    except Exception as e:
        log("Error during frontend install: ", e, type(e), lvl=error, exc=True)

    log('Components after lookup:', sorted(list(components.keys())))

    def _update_frontends(install=True):
        log("Checking unique frontend locations: ", components, lvl=debug)

        imports = []
        modules = []

        installation_packages = []

        log(components, pretty=True)

        for package_name, component in components.items():
            if 'frontend' in component:
                origin = component['frontend']
                method = component['method']
                package = component.get('package', None)

                target = os.path.join(frontend_root, 'src', 'components', package_name)
                target = os.path.normpath(target)

                if install:
                    if method == 'folder':
                        requirements_file = os.path.join(origin, 'requirements.txt')

                        if os.path.exists(requirements_file):
                            log("Adding package dependencies for", package_name, lvl=debug)
                            with open(requirements_file, 'r') as f:
                                for line in f.readlines():
                                    installation_packages.append(line.replace("\n", ""))
                    elif method == 'resources':
                        pkg = pkg_resources.Requirement.parse(package)
                        if pkg_resources.resource_exists(pkg, 'frontend/requirements.txt'):
                            for line in pkg_resources.resource_string(pkg, 'frontend/requirements.txt'):
                                installation_packages.append(line.replace("\n", ""))

                log("Copying:", origin, target, lvl=debug)
                if method == 'folder':
                    copy_directory_tree(origin, target)
                elif method == 'resources':
                    copy_resource_tree(package, 'frontend', target)

                for module_filename in glob(target + '/*.module.js'):
                    module_name = os.path.basename(module_filename).split(".module.js")[0]
                    line = u"import {s} from './components/{p}/{s}.module';\nmodules.push({s});\n".format(
                        s=module_name, p=package_name)

                    if module_name not in modules:
                        imports += line
                        modules.append(module_name)
            else:
                log("Module without frontend:", package_name, component,
                    lvl=debug)

        if install:
            command_line = ['npm', 'install'] + installation_packages
            log("Running", command_line, lvl=verbose)

            # TODO: Switch to i.t.run_process
            installer = Popen(command_line, cwd=frontend_root)
            installer_output, installer_error = installer.communicate()

            installer.wait()

            log("Frontend installing done: ", installer_output, installer_error, lvl=debug)

        with open(os.path.join(frontend_root, 'src', 'main.tpl.js'), "r") as f:
            main = "".join(f.readlines())

        parts = main.split("/* COMPONENT SECTION */")
        if len(parts) != 3:
            log("Frontend loader seems damaged! Please check!",
                lvl=critical)
            return

        try:
            with open(os.path.join(frontend_root, 'src', 'main.js'),
                      "w") as f:
                f.write(parts[0])
                f.write("/* COMPONENT SECTION:BEGIN */\n")
                for line in imports:
                    f.write(line)
                f.write("/* COMPONENT SECTION:END */\n")
                f.write(parts[2])
        except Exception as e:
            log("Error during frontend package info writing. Check "
                "permissions! ", e, lvl=error)

    def _rebuild_frontend():
        log("Starting frontend build.", lvl=warn)

        # TODO: Switch to i.t.run_process
        builder = Popen(["npm", "run", build_type], cwd=frontend_root)
        builder_output, builder_error = builder.communicate()
        try:
            builder.wait()
        except Exception as e:
            log("Error during frontend build", e, type(e),
                exc=True, lvl=error)
            return

        log("Frontend build done: ", builder_output, builder_error, lvl=debug)

        try:
            copy_directory_tree(os.path.join(frontend_root, build_type),
                                frontend_target, hardlink=False)
            copy_directory_tree(os.path.join(frontend_root, 'assets'),
                                os.path.join(frontend_target, 'assets'),
                                hardlink=False)
        except PermissionError:
            log('No permission to change:', frontend_target, lvl=error)

        log("Frontend deployed")

    log("Checking component frontend bits in ", frontend_root,
        lvl=verbose)

    _update_frontends(install=install)
    if forcerebuild:
        _rebuild_frontend()

    log("Done: Install Frontend")

    # We have to find a way to detect if we need to rebuild (and
    # possibly wipe) stuff. This maybe the case, when a frontend
    # module has been updated/added/removed.
