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
Frontend building process.

Since this involves a lot of javascript handling, it is best advised to not
directly use any of the functionality except `install_frontend` and maybe
`rebuild_frontend`.
"""

import json
import os
import shutil
from glob import glob
from shutil import copy

import pkg_resources
from isomer.logger import isolog, debug, verbose, warn, error, critical
from isomer.misc.path import get_path
from isomer.tool import run_process


def log(*args, **kwargs):
    """Log as builder emitter"""
    kwargs.update({"emitter": "BUILDER", "frame_ref": 2})
    isolog(*args, **kwargs)


# TODO: Move the copy resource/directory tree operations to a utility lib


def copy_directory_tree(root_src_dir: str, root_dst_dir: str, hardlink: bool = True):
    """Copies a whole directory tree

    :param root_src_dir: Source filesystem location
    :param root_dst_dir: Target filesystem location
    :param hardlink: Create hardlinks instead of copying (experimental)
    """

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
                        log("Removing frontend link:", dst_file, lvl=verbose)
                        os.remove(dst_file)
                    else:
                        log("Overwriting frontend file:", dst_file, lvl=verbose)
                else:
                    log("Target not existing:", dst_file, lvl=verbose)
            except PermissionError as e:
                log("No permission to remove target:", e, lvl=error)

            try:
                if hardlink:
                    log("Hardlinking ", src_file, dst_dir, lvl=verbose)
                    os.link(src_file, dst_file)
                else:
                    log("Copying ", src_file, dst_dir, lvl=verbose)
                    copy(src_file, dst_dir)
            except PermissionError as e:
                log(
                    " No permission to create target %s for frontend:"
                    % ("link" if hardlink else "copy"),
                    dst_dir,
                    e,
                    lvl=error,
                )
            except Exception as e:
                log(
                    "Error during",
                    "link" if hardlink else "copy",
                    "creation:",
                    type(e),
                    e,
                    lvl=error,
                )

            log("Done linking", root_dst_dir, lvl=verbose)


def copy_resource_tree(package: str, source: str, target: str):
    """Copies a whole resource tree

    :param package: Package object with resources
    :param source: Source folder inside package resources
    :param target: Filesystem destination
    """

    pkg = pkg_resources.Requirement.parse(package)

    log(
        "Copying component frontend tree for %s to %s (%s)" % (package, target, source),
        lvl=debug,
    )

    if not os.path.exists(target):
        os.mkdir(target)

    for item in pkg_resources.resource_listdir(pkg, source):
        log("Handling resource item:", item, lvl=verbose)

        if item in ("__pycache__", "__init__.py"):
            continue

        target_name = os.path.join(
            target, source.split("frontend")[1].lstrip("/"), item
        )
        log("Would copy to:", target_name, lvl=verbose)

        if pkg_resources.resource_isdir(pkg, source + "/" + item):
            log("Creating subdirectory:", target_name, lvl=debug)
            try:
                os.mkdir(target_name)
            except FileExistsError:
                log("Subdirectory already exists, ignoring", lvl=debug)

            log("Recursing resource subdirectory:", source + "/" + item, lvl=debug)
            copy_resource_tree(package, source + "/" + item, target)
        else:
            log("Copying resource file:", source + "/" + item, lvl=debug)
            with open(target_name, "wb") as f:
                f.write(pkg_resources.resource_string(pkg, source + "/" + item))


def get_frontend_locations(development):
    """Determine the frontend target and root locations.
    The root is where the complete source code for the frontend will be
    assembled, whereas the target is its installation directory after
    building
    :param development: If True, uses the development frontend server location
    :return:
    """

    log("Checking frontend location", lvl=debug)

    if development is True:
        log("Using development frontend location")
        root = os.path.realpath(
            os.path.dirname(os.path.realpath(__file__)) + "/../../frontend"
        )
        target = get_path("lib", "frontend-dev")
        if not os.path.exists(target):
            log("Creating development frontend folder", lvl=debug)
            try:
                os.makedirs(target)
            except PermissionError:
                log(
                    "Cannot create development frontend target! "
                    "Check permissions on",
                    target,
                )
                return None, None
    else:
        log("Using production frontend location")
        root = get_path("lib", "repository/frontend")
        target = get_path("lib", "frontend")

    log("Frontend components located in", root, lvl=debug)

    return root, target


def generate_component_folders(folder):
    """If not existing, create the components' holding folder inside the
    frontend source tree

    :param folder: Target folder in the frontend's source, where frontend
    modules will be copied to
    """

    if not os.path.isdir(folder):
        log("Creating new components folder")
        os.makedirs(folder)
    else:
        log("Clearing components folder")
        for thing in os.listdir(folder):
            target = os.path.join(folder, thing)

            try:
                shutil.rmtree(target)
            except NotADirectoryError:
                os.unlink(target)
            except PermissionError:
                log(
                    "Cannot remove data in old components folder! "
                    "Check permissions in",
                    folder,
                    thing,
                    lvl=warn,
                )


def get_components(frontend_root):
    """Iterate over all installed isomer modules to find all the isomer
    components frontends and their dependencies
    :param frontend_root: Frontend source root directory
    :return:
    """

    def inspect_entry_point(component_entry_point):
        """Use pkg_tools to inspect an installed module for its metadata

        :param component_entry_point: A single entrypoint for an isomer module
        """

        name = component_entry_point.name
        package = component_entry_point.dist.project_name
        location = component_entry_point.dist.location
        loaded = component_entry_point.load()

        log("Package:", package, lvl=debug)

        log(
            "Entry point: ",
            component_entry_point,
            name,
            component_entry_point.resolve().__module__,
            lvl=debug,
        )
        component_name = component_entry_point.resolve().__module__.split(".")[1]

        log("Loaded: ", loaded, lvl=verbose)
        component = {
            "location": location,
            "version": str(component_entry_point.dist.parsed_version),
            "description": loaded.__doc__,
            "package": package,
        }

        try:
            pkg = pkg_resources.Requirement.parse(package)
            log("Checking component data resources", lvl=debug)
            try:
                resources = pkg_resources.resource_listdir(pkg, "frontend")
            except FileNotFoundError:
                log("Component does not have a frontend", lvl=debug)
                resources = []

            if len(resources) > 0:
                component["frontend"] = resources
                component["method"] = "resources"
        except ModuleNotFoundError:
            frontend = os.path.join(location, "frontend")
            log("Checking component data folders ", frontend, lvl=verbose)
            if os.path.isdir(frontend) and frontend != frontend_root:
                component["frontend"] = frontend
                component["method"] = "folder"

        if "frontend" not in component:
            log(
                "Component without frontend directory:",
                component,
                lvl=debug,
            )
            return None, None
        return component_name, component

    log("Updating frontend components")

    inspected_components = {}
    try:
        from pkg_resources import iter_entry_points

        entry_point_tuple = (
            iter_entry_points(group="isomer.sails", name=None),
            iter_entry_points(group="isomer.components", name=None),
        )

        for iterator in entry_point_tuple:
            for entry_point in iterator:
                try:
                    inspectable_package = entry_point.dist.project_name

                    if inspectable_package == "isomer":
                        log("Not inspecting base isomer package", pretty=True)
                        continue

                    inspected_name, inspected_component = inspect_entry_point(
                        entry_point)

                    if inspected_name is not None and \
                        inspected_component is not None:
                        inspected_components[inspected_name] = inspected_component
                except Exception as e:
                    log(
                        "Could not inspect entrypoint: ",
                        e,
                        type(e),
                        entry_point,
                        iterator,
                        lvl=error,
                        exc=True,
                    )

        # frontends = iter_entry_points(group='isomer.frontend', name=None)
        # for entrypoint in frontends:
        #     name = entrypoint.name
        #     location = entrypoint.dist.location
        #
        #     log('Frontend entrypoint:', name, location, entrypoint, lvl=hilight)

    except Exception as e:
        log("Error during frontend install: ", e, type(e), lvl=error, exc=True)

    component_list = list(inspected_components.keys())
    log("Components after lookup (%i):" % len(component_list),
        sorted(component_list))

    return inspected_components


def update_frontends(frontend_components: dict, frontend_root: str, install: bool):
    """Installs all found entrypoints and returns the list of all required
    dependencies

    :param frontend_root: Frontend source root directory
    :param install: If true, collect installable dependencies
    :param frontend_components: Dictionary with component names and metadata
    :return:
    """

    def get_component_dependencies(pkg_method: str, pkg_origin: str, pkg_name: str,
                                   pkg_object):
        """Inspect components resource or requirement strings to collect
        their dependencies

        :param pkg_method: Method how the dependencies are stored,
            either 'folder' or 'resources'. Folder expects a requirements.txt
            with javascript dependencies, whereas resources expects them
            inside the setup.py of the module
        :param pkg_origin: Folder with the module's frontend root
        :param pkg_name: Name of the entrypoint
        :param pkg_object: Entrypoint object
        """

        packages = []

        if pkg_method == "folder":
            requirements_file = os.path.join(pkg_origin, "requirements.txt")

            if os.path.exists(requirements_file):
                log(
                    "Adding package dependencies for",
                    pkg_name,
                    lvl=debug,
                )
                with open(requirements_file, "r") as f:
                    for requirements_line in f.readlines():
                        packages.append(requirements_line.replace("\n", ""))
        elif pkg_method == "resources":
            log("Getting resources:", pkg_object)
            resource = pkg_resources.Requirement.parse(pkg_object)
            if pkg_resources.resource_exists(
                resource, "frontend/requirements.txt"
            ):
                resource_string = pkg_resources.resource_string(
                    resource, "frontend/requirements.txt"
                )

                # TODO: Not sure if decoding to ascii is a smart
                #  idea for npm package names.
                for resource_line in (
                    resource_string.decode("ascii").rstrip("\n").split("\n")
                ):
                    log("Resource string:", resource_line)
                    packages.append(resource_line.replace("\n", ""))

        return packages

    def install_frontend_data(pkg_object, pkg_name: str):
        """Gather all frontend components' data files and while inspecting
        the components, collect their dependencies, as well, if frontend
        installation has been requested

        :param pkg_object: Setuptools entrypoint descriptor
        :param pkg_name: Name of the entrypoint
        """

        log(type(pkg_object), lvl=critical)

        origin = pkg_object["frontend"]
        method = pkg_object["method"]
        package_object = pkg_object.get("package", None)
        target = os.path.join(frontend_root, "src", "components", pkg_name)
        target = os.path.normpath(target)

        if install:
            module_dependencies = get_component_dependencies(
                method, origin, pkg_name,
                package_object
            )
        else:
            module_dependencies = []

        log("Copying:", origin, target, lvl=debug)
        if method == "folder":
            copy_directory_tree(origin, target)
        elif method == "resources":
            copy_resource_tree(package_object, "frontend", target)

        for module_filename in glob(target + "/*.module.js"):
            module_name = os.path.basename(module_filename).split(".module.js")[
                0
            ]
            module_line = (
                u"import {s} from './components/{p}/{s}.module';\n"
                u"modules.push({s});\n".format(s=module_name, p=pkg_name)
            )

            yield module_dependencies, module_line, module_name

    log("Checking unique frontend locations: ", frontend_components, lvl=debug,
        pretty=True)

    importable_modules = []
    dependency_packages = []
    modules = []  # For checking if we already got it

    for package_name, package_component in frontend_components.items():
        if "frontend" in package_component:
            for dependencies, import_line, module in install_frontend_data(
                package_component, package_name):
                if module not in modules:
                    modules += module
                    if len(dependencies) > 0:
                        dependency_packages += dependencies
                    importable_modules.append(import_line)

        else:
            log("Module without frontend:", package_name, package_component,
                lvl=debug)

    log("Dependencies:", dependency_packages, "Component Imports:",
        importable_modules, pretty=True,
        lvl=debug)

    return dependency_packages, importable_modules


def get_sails_dependencies(root):
    """Get all core user interface (sails) dependencies

    :param root: Frontend source root directory
    """

    packages = []

    with open(os.path.join(root, 'package.json'), 'r') as f:
        package_json = json.load(f)

    log('Adding deployment packages', lvl=verbose)
    for package, version in package_json['dependencies'].items():
        packages.append("@".join([package, version]))

    log('Adding development packages', lvl=verbose)
    for package, version in package_json['devDependencies'].items():
        packages.append("@".join([package, version]))

    log('Found %i isomer base dependencies' % len(packages), lvl=debug)
    return packages


def install_dependencies(dependency_list: list, frontend_root: str):
    """Instruct npm to install a list of all dependencies

    :param frontend_root: Frontend source root directory
    :param dependency_list: List of javascript dependency packages
    """

    log("Installing dependencies:", dependency_list, lvl=debug)
    command_line = ["npm", "install", "--no-save"] + dependency_list

    log("Using npm in:", frontend_root, lvl=debug)
    success, installer = run_process(frontend_root, command_line)

    if success:
        log("Frontend installing done.", lvl=debug)
    else:
        log("Could not install dependencies:", installer)


def write_main(importable_modules: list, root: str):
    """With the gathered importable modules, populate the main frontend
    loader and write it to the frontend's root

    :param importable_modules: List of importable javascript module files
    :param root: Frontend source root directory
    """

    log("Writing main frontend loader", lvl=debug)
    with open(os.path.join(root, "src", "main.tpl.js"), "r") as f:
        main = "".join(f.readlines())

    parts = main.split("/* COMPONENT SECTION */")
    if len(parts) != 3:
        log("Frontend loader seems damaged! Please check!", lvl=critical)
        return

    try:
        with open(os.path.join(root, "src", "main.js"), "w") as f:
            f.write(parts[0])
            f.write("/* COMPONENT SECTION:BEGIN */\n")
            for line in importable_modules:
                f.write(line)
            f.write("/* COMPONENT SECTION:END */\n")
            f.write(parts[2])
    except Exception as write_exception:
        log(
            "Error during frontend package info writing. Check " "permissions! ",
            write_exception,
            lvl=error,
        )


def rebuild_frontend(root: str, target: str, build_type: str):
    """Instruct npm to rebuild the frontend

    :param root: Frontend source root directory
    :param target: frontend build target installation directory
    :param build_type: Type of frontend build, either 'dist' or 'build'
    :return:

    """

    log("Starting frontend build.", lvl=warn)

    # TODO: Switch to i.t.run_process
    log("Using npm in:", root, lvl=debug)
    command = ["npm", "run", build_type]
    success, builder_output = run_process(root, command)

    if success is False:
        log("Error during frontend build:", builder_output, lvl=error)
        return

    log("Frontend build done: ", builder_output, lvl=debug)

    try:
        copy_directory_tree(
            os.path.join(root, build_type), target, hardlink=False
        )
        copy_directory_tree(
            os.path.join(root, "assets"),
            os.path.join(target, "assets"),
            hardlink=False,
        )
    except PermissionError:
        log("No permission to change:", target, lvl=error)

    log("Frontend deployed")


def install_frontend(
    force_rebuild: bool = False,
    install: bool = True,
    development: bool = False,
    build_type: str = "dist",
):
    """Builds and installs the frontend.

    The process works like this:

    * Find the frontend locations (source root and target)
    * Generate the target component folders to copy modules' frontend sources to
    * Gather all component meta data
    * Collect all dependencies (when installing them is desired) and their module
      imports
    * If desired, install all dependencies
    * Write the frontend main loader with all module entrypoints
    * Run npm build `BUILD_TYPE` and copy all resulting files to the frontend target
      folder

    :param force_rebuild: Trigger a rebuild of the sources.
    :param install: Trigger installation of the frontend's dependencies
    :param development: Use development frontend server locations
    :param build_type: Type of frontend build, either 'dist' or 'build'
    """

    frontend_root, frontend_target = get_frontend_locations(development)

    if frontend_root is None or frontend_target is None:
        log("Cannot determine either frontend root or target, please inspect",
            lvl=error)
        return

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    components = get_components(frontend_root)

    installation_packages, imports = update_frontends(
        components, frontend_root, install
    )

    if install:
        installation_packages += get_sails_dependencies(frontend_root)
        install_dependencies(installation_packages, frontend_root)

    write_main(imports, frontend_root)

    if force_rebuild:
        rebuild_frontend(frontend_root, frontend_target, build_type)

    log("Done: Install Frontend")

    # TODO: We have to find a way to detect if we need to rebuild (and
    #  possibly wipe) stuff. This maybe the case, when a frontend
    #  module has been updated/added/removed.
