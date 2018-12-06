#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
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

"""
Frontend building process
"""

import os
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
    kwargs.update({'emitter': 'BUILDER', 'frame_ref': 2})
    isolog(*args, **kwargs)


def copytree(root_src_dir, root_dst_dir, hardlink=True):
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


def install_frontend(instance='default', forcereload=False, forcerebuild=False,
                     forcecopy=True, install=True, development=False, build_type='dist'):
    """Builds and installs the frontend"""

    log("Updating frontend components")
    components = {}
    loadable_components = {}

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

    if True:  # try:
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
                    location = entry_point.dist.location
                    loaded = entry_point.load()

                    log("Entry point: ", entry_point,
                        name,
                        entry_point.resolve().__module__, lvl=debug)
                    component_name = entry_point.resolve().__module__.split('.')[1]

                    log("Loaded: ", loaded, lvl=verbose)
                    comp = {
                        'location': location,
                        'version': str(entry_point.dist.parsed_version),
                        'description': loaded.__doc__
                    }

                    frontend = os.path.join(location, 'frontend')
                    log("Checking component frontend parts: ",
                        frontend, lvl=verbose)
                    if os.path.isdir(frontend) and frontend != frontend_root:
                        comp['frontend'] = frontend
                    else:
                        log("Component without frontend "
                            "directory:", comp, lvl=debug)

                    components[component_name] = comp
                    loadable_components[component_name] = loaded

                    log("Loaded component:", comp, lvl=verbose)

                except Exception as e:
                    log("Could not inspect entrypoint: ", e,
                        type(e), entry_point, iterator, lvl=error,
                        exc=True)

        frontends = iter_entry_points(group='isomer.frontend', name=None)
        for entrypoint in frontends:
            name = entrypoint.name
            location = entrypoint.dist.location

            log('Frontend entrypoint:', name, location, entrypoint, lvl=hilight)

    # except Exception as e:
    #    isomerlog("Error: ", e, type(e), lvl=error, exc=True)
    #    return

    log('Components after lookup:', sorted(list(components.keys())))

    def _update_frontends(install=True):
        log("Checking unique frontend locations: ",
            loadable_components, lvl=debug)

        importlines = []
        modules = []

        for name, component in components.items():
            if 'frontend' in component:
                origin = component['frontend']

                target = os.path.join(frontend_root, 'src', 'components',
                                      name)
                target = os.path.normpath(target)

                if install:
                    reqfile = os.path.join(origin, 'requirements.txt')

                    if os.path.exists(reqfile):
                        # TODO: Speed this up by collecting deps first then doing one single install call
                        log("Installing package dependencies for", name, lvl=debug)
                        with open(reqfile, 'r') as f:
                            cmdline = ["npm", "install"]
                            for line in f.readlines():
                                cmdline.append(line.replace("\n", ""))

                            log("Running", cmdline, lvl=verbose)
                            npminstall = Popen(cmdline, cwd=frontend_root)
                            out, err = npminstall.communicate()

                            npminstall.wait()

                            log("Frontend installing done: ", out,
                                err, lvl=debug)

                # if target in ('/', '/boot', '/usr', '/home', '/root',
                # '/var'):
                #    log("Unsafe frontend deletion target path, "
                #        "NOT proceeding! ", target, lvl=critical)

                log("Copying:", origin, target, lvl=debug)

                copytree(origin, target)

                for module_filename in glob(target + '/*.module.js'):
                    module_name = os.path.basename(module_filename).split(".module.js")[0]
                    line = u"import {s} from './components/{p}/{s}.module';\nmodules.push({s});\n".format(
                        s=module_name, p=name)
                    if module_name not in modules:
                        importlines += line
                        modules.append(module_name)
            else:
                log("Module without frontend:", name, component,
                    lvl=debug)

        with open(os.path.join(frontend_root, 'src', 'main.tpl.js'),
                  "r") as f:
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
                for line in importlines:
                    f.write(line)
                f.write("/* COMPONENT SECTION:END */\n")
                f.write(parts[2])
        except Exception as e:
            log("Error during frontend package info writing. Check "
                "permissions! ", e, lvl=error)

    def _rebuild_frontend():
        log("Starting frontend build.", lvl=warn)

        npmbuild = Popen(["npm", "run", build_type], cwd=frontend_root)
        out, err = npmbuild.communicate()
        try:
            npmbuild.wait()
        except Exception as e:
            log("Error during frontend build", e, type(e),
                exc=True, lvl=error)
            return

        log("Frontend build done: ", out, err, lvl=debug)

        try:
            copytree(os.path.join(frontend_root, build_type),
                     frontend_target, hardlink=False)
            copytree(os.path.join(frontend_root, 'assets'),
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
