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

Test Isomer Environment Management
==================================



"""

import os
import pytest

from isomer.tool.etc import load_instance
from isomer.tool.tool import isotool

import warnings

# TODO: The numbering is here because pytest-dependency is missing dependency test
#  sorting. Remove when the PR ( https://github.com/RKrahl/pytest-dependency/pull/44 )
#  has been integrated
@pytest.mark.dependency()
def test_00_environment_clear():

    """Creates a new default instances and clears it without archiving"""
    pytest.reset_base()

    _ = pytest.run_cli(isotool, ['instance', 'create'], full_log=True)

    assert os.path.exists('/tmp/isomer-test/etc/isomer/instances/' +
                          pytest.INSTANCENAME + '.conf')
    assert not os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
                              pytest.INSTANCENAME + '/green')

    result = pytest.run_cli(isotool, ['environment', 'clear', '--no-archive'])

    warnings.warn(result.output)

    # assert os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    # assert os.path.exists('/tmp/isomer-test/var/cache/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    # assert os.path.exists('/tmp/isomer-test/var/local/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    assert result.exit_code == 0


@pytest.mark.dependency(depends=["test_00_environment_clear"])
def test_01_install():
    """Creates a new default instances and clears it without archiving"""
    pytest.reset_base(unset_instance=True)
    import os
    import pwd

    def get_username():
        """Return current username"""
        return pwd.getpwuid(os.getuid())[0]

    _ = pytest.run_cli(isotool, ['instance', 'create'], full_log=True)
    _ = pytest.run_cli(isotool, ['instance', 'set', 'user', get_username()],
                       full_log=True)
    _ = pytest.run_cli(isotool, ['environment', 'clear', '--no-archive'], full_log=True)

    # assert os.path.exists('/tmp/isomer-test/etc/isomer/instances/' +
    #                       pytest.INSTANCENAME + '.conf')
    # assert os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
    #                       pytest.INSTANCENAME + '/green')

    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    result = pytest.run_cli(
        isotool,
        ['environment', 'install', '--no-sudo', '--source', 'copy',
         '--url', repo_path, '--skip-provisions', '--skip-frontend'],
        full_log=True
    )

    assert result.exit_code == 0

    # assert os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    # assert os.path.exists('/tmp/isomer-test/var/cache/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    # assert os.path.exists('/tmp/isomer-test/var/local/isomer/' +
    #                       pytest.INSTANCENAME + '/green')
    # assert os.path.exists(
    #     '/tmp/isomer-test/var/lib/isomer/' +
    #     pytest.INSTANCENAME + '/green/venv/bin/python3')
    # assert os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
    #                       pytest.INSTANCENAME + '/green/venv/bin/iso')
    # assert os.path.exists('/tmp/isomer-test/var/lib/isomer/' +
    #                       pytest.INSTANCENAME + '/green/repository')
    # assert os.path.exists(
    #     '/tmp/isomer-test/var/lib/isomer/' +
    #     pytest.INSTANCENAME + '/green/repository/frontend')

    instance_configuration = load_instance(pytest.INSTANCENAME)
    environment = instance_configuration['environments']['green']

    assert environment['installed'] is True
    assert environment['provisioned'] is False
    assert environment['migrated'] is True
    assert environment['frontend'] is False
    assert environment['tested'] is False
    assert environment['database'] == pytest.INSTANCENAME + '_green'

    if result.exit_code != 0:
        print(result.output)
        print("For more information on possibly failed subtasks, "
              "consult /tmp/isomer_test_run_cli_logfile")
