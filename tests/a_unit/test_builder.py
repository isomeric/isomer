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
Hackerfleet Operating System - Backend

Test Isomer Tools
===============



"""

import os
import shutil
from pathlib import Path

import pytest
from isomer.misc.path import set_instance
from isomer.ui.builder import copy_directory_tree, copy_resource_tree, \
    get_frontend_locations, generate_component_folders, get_components, \
    update_frontends, get_sails_dependencies, write_main

try:
    import isomer.test as test
except ImportError:
    test = None

has_test_module = pytest.mark.skipif(
    test is None,
    reason="isomer-test-module not installed. See "
           "https://isomer.readthedocs.io/en/latest/dev/system/backend/modularity.html"
           "#modules"
)


def test_copy_directory_tree():
    os.makedirs("/tmp/isomer-test/copy_directory_tree/foo/bar", exist_ok=True)
    with open("/tmp/isomer-test/copy_directory_tree/foo/bar/ham", "w") as f:
        f.write("spam!")

    copy_directory_tree(
        "/tmp/isomer-test/copy_directory_tree",
        "/tmp/isomer-test/copy_directory_tree_test"
    )

    assert os.path.exists("/tmp/isomer-test/copy_directory_tree_test/foo/bar/ham")


def test_move_directory_tree():
    source = "/tmp/isomer-test/copy_directory_tree"
    target = "/tmp/isomer-test/copy_directory_tree_test"

    source_file = os.path.join(source, "foo/bar/ham")
    target_file = os.path.join(target, "foo/bar/ham")

    os.makedirs(os.path.join(source, "foo/bar"), exist_ok=True)
    with open(source_file, "w") as f:
        f.write("spam!")

    shutil.rmtree(target, ignore_errors=True)

    copy_directory_tree(
        source,
        target,
        move=True
    )

    assert os.path.exists(target_file)
    assert not os.path.exists(source_file)


def test_get_frontend_locations_development():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(True)

    assert frontend_root == os.path.join(
        str(Path(__file__).parents[2]), 'frontend'
    )
    assert frontend_target == \
           '/tmp/isomer-test/var/lib/isomer/test-instance/test/frontend-dev'


def test_get_frontend_locations():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(False)
    assert frontend_root == \
           "/tmp/isomer-test/var/lib/isomer/test-instance/test/repository/frontend"
    assert frontend_target == \
           "/tmp/isomer-test/var/lib/isomer/test-instance/test/frontend"


def test_generate_component_folders():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(False)

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    assert os.path.exists(component_folder)

    old_file = os.path.join(component_folder, "ham")

    with open(old_file, "w") as f:
        f.write("spam")

    generate_component_folders(component_folder)

    assert not os.path.exists(old_file)


@has_test_module
def test_copy_resource_tree():
    dest = "/tmp/isomer-test/copy_resource_test"
    os.makedirs(dest, exist_ok=True)

    from pkg_resources import get_entry_info

    pkg_object = get_entry_info("isomer-test-module", "isomer.components", "testmanager")

    # pytest.exit(crap)

    copy_resource_tree("isomer-test-module", "frontend", dest)

    assert os.path.exists(os.path.join(dest, "test.module.js"))


@has_test_module
def test_get_components():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(False)

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    components = get_components(frontend_root)
    assert isinstance(components, dict)

    assert 'test' in components


@has_test_module
def test_update_frontends():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(False)

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    components = get_components(frontend_root)

    installation_packages, imports = update_frontends(
        components, frontend_root, True
    )

    assert "test-npm-update" in installation_packages
    assert "import test from './components/test/test.module';\n" \
           "modules.push(test);\n" in imports


@has_test_module
def test_get_sails_dependencies():
    frontend_root, _ = get_frontend_locations(True)
    installation_packages = get_sails_dependencies(frontend_root)

    assert "angular" in ";".join(installation_packages)


@has_test_module
def test_write_main():
    imports = ["IMPORTTEST"]
    root, _ = get_frontend_locations(True)
    source_file = os.path.join(root, "src/main.tpl.js")
    target = os.path.join("/tmp/isomer-test/", "src")
    target_file = os.path.join(target, "main.tpl.js")

    os.makedirs(target, exist_ok=True)
    try:
        os.unlink(target_file)
    except FileNotFoundError:
        pass
    except OSError:
        pytest.fail("Could not delete existing frontend loader")

    shutil.copy(source_file, target_file)

    write_main(imports, "/tmp/isomer-test")

    with open(os.path.join(target, "main.js")) as f:
        content = f.read()

    assert "IMPORTTEST" in content
