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
Isomer - Backend

Test Isomer Frontend Builder
============================


"""

import os
import pytest

from isomer.ui.builder import get_frontend_locations, generate_component_folders, \
    get_components, update_frontends, get_sails_dependencies, install_dependencies, \
    write_main, install_frontend

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

# TODO: These last tests depend on working with the current copy of the source.
#  This is especially bad, if there are isomer modules installed, which might
#  bring in further dependencies.


@has_test_module
def test_install_dependencies():

    frontend_root, frontend_target = get_frontend_locations(True)

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    components = get_components(frontend_root)

    installation_packages, imports = update_frontends(
        components, frontend_root, True
    )

    installation_packages += get_sails_dependencies(frontend_root)
    install_dependencies(installation_packages, frontend_root)

    target = os.path.join(frontend_root, "node_modules")

    assert os.path.exists(target)
    assert os.path.exists(os.path.join(target, "test-npm-update"))


@has_test_module
def test_rebuild_frontend():
    frontend_root, frontend_target = get_frontend_locations(True)

    component_folder = os.path.join(frontend_root, "src", "components")
    generate_component_folders(component_folder)

    components = get_components(frontend_root)

    installation_packages, imports = update_frontends(
        components, frontend_root, True
    )

    installation_packages += get_sails_dependencies(frontend_root)
    install_dependencies(installation_packages, frontend_root)

    write_main(imports, frontend_root)

    install_frontend(True, True, True, "build")

    assert os.path.exists(frontend_target)
    assert os.path.exists(os.path.join(frontend_target, "index.html"))
    assert os.path.exists(os.path.join(frontend_target, "assets"))