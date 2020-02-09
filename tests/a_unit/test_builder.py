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

import pytest
from isomer.misc.path import set_instance

from isomer.ui.builder import copy_directory_tree, copy_resource_tree, \
    get_frontend_locations, generate_component_folders, get_components, \
    update_frontends, get_sails_dependencies, install_dependencies,write_main, \
    rebuild_frontend

try:
    import isomer.test as test
except ImportError:
    test = None

has_test_module = pytest.mark.skipif(
    test is not None,
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


def test_get_frontend_locations_development():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(True)
    assert frontend_root == '/home/riot/src/isomer/isomer_master/frontend'
    assert frontend_target == '/tmp/isomer-test/var/lib/isomer/test-instance/test/frontend-dev'


def test_get_frontend_locations():
    set_instance("test-instance", "test", "/tmp/isomer-test")
    frontend_root, frontend_target = get_frontend_locations(False)
    assert frontend_root == "/tmp/isomer-test/var/lib/isomer/test-instance/test/repository/frontend"
    assert frontend_target == "/tmp/isomer-test/var/lib/isomer/test-instance/test/frontend"


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

    package_object = pkg_object.get("package", None)
    copy_resource_tree(package_object, "iso", dest)

    assert os.path.exists(os.path.join(dest, "iso"))


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
    assert True


@has_test_module
def test_get_sails_dependencies():
    assert True


@has_test_module
def test_install_dependencies():
    assert True


@has_test_module
def test_write_main():
    assert True


@has_test_module
def test_rebuild_frontend():
    assert True


@has_test_module
def test_install_frontend():
    assert True
