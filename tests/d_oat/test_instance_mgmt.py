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
Isomer Application Framework - Backend

Test Isomer Instance Management
===============================



"""

from . import reset_base, run_cli

from pprint import pprint

import pytest
import os

from isomer.misc.path import set_instance, get_path
from isomer.tool.etc import load_instance

from isomer.tool.tool import isotool


def test_path_prefix():
    """Tests correct package importing - critical test! If this one fails, it cancels the whole run."""

    result = True
    set_instance('', None, '')

    default = get_path('lib', '', ensure=False)
    result &= default == '/var/lib/isomer'

    set_instance('default', 'green')

    unset_prefix = get_path('lib', '', ensure=False)
    result &= unset_prefix == '/var/lib/isomer/default/green'

    set_instance('default', 'green', prefix='/foo/bar/')

    prefixed = get_path('lib', '', ensure=False)
    result &= prefixed == '/foo/bar/var/lib/isomer/default/green'

    if result is False:
        pytest.exit('Default:' + default + ' Unset:' + unset_prefix + ' Set:' + prefixed +
                    'Path prefixing is broken! Not continuing until you fix "isomer.misc.path"!')


def test_instance_create():
    """On a blank setup, tests if creating an instance works"""

    reset_base()

    result = run_cli(isotool, ['instance', 'create'])

    assert result.exit_code == 0

    assert os.path.exists('/tmp/isomer-test/etc/isomer/instances/default.conf')


def test_instance_info():
    """Creates a new default instance and check the info command output against it"""
    reset_base()

    _ = run_cli(isotool, ['instance', 'create'])

    result = run_cli(isotool, ['instance', 'info'])

    assert result.exit_code == 0

    assert 'Instance configuration' in result.output
    assert 'Active environment' in result.output


def test_instance_list():
    """Creates two new instances and checks if the list command lists both"""
    reset_base()

    run_cli(isotool, ['--instance', 'bar', 'instance', 'create'], full_log=True)
    run_cli(isotool, ['--instance', 'foo', 'instance', 'create'], full_log=True)

    result = run_cli(isotool, ['instance', 'list'])

    assert result.exit_code == 0

    pprint(result.output)

    assert 'foo' in result.output
    assert 'bar' in result.output


def test_instance_set():
    """Creates a new default instances and checks if setting a parameter works"""
    reset_base()

    _ = run_cli(isotool, ['instance', 'create'])

    new_config = load_instance('default')

    assert new_config['quiet'] is True

    result = run_cli(isotool, ['instance', 'set', 'quiet', 'false'])

    new_config = load_instance('default')

    assert result.exit_code == 0
    assert new_config['quiet'] is False


def test_instance_clear():
    """Creates a new default instances and checks if clearing it works"""
    reset_base()

    _ = run_cli(isotool, ['instance', 'create'])

    result = run_cli(isotool, ['instance', 'clear', '--force', '--no-archive'])
    pprint(result.output)

    assert result.exit_code == 0
    # TODO: Verify that the instance has been cleared (Probably: fill it first)
