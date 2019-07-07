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

Operational Acceptance Testing
==============================

.. warning:: These tests take a long time!

Citing :cite:`wiki:oat` about OAT:

    Operational acceptance testing (OAT) is used to conduct operational readiness (pre-release) of a product, service,
    or system as part of a quality management system. [..] This type of testing focuses on the operational readiness of
    the system to be supported, and/or to become part of the production environment.


.. bibliography:: ../../refs.bib
"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import os
import shutil
from pprint import pprint

from click.testing import CliRunner
from isomer.misc.path import set_etc_path, set_instance

colors = False


def reset_base():
    """Prepares a testing folder and sets Isomer's base to that"""
    if os.path.exists('/tmp/isomer-test'):
        shutil.rmtree('/tmp/isomer-test')

    os.makedirs('/tmp/isomer-test/etc/isomer/instances')
    os.makedirs('/tmp/isomer-test/var/log/isomer')

    set_etc_path('/tmp/isomer-test/etc/isomer')
    set_instance('foobar', 'green', '/tmp/isomer-test/')


def run_cli(cmd, args, full_log=False):
    """Runs a command"""

    if colors is False:
        args.insert(0, '-nc')

    if full_log:
        log_args = ['--clog', '5', '--flog', '5', '--log-path', '/tmp/isomer-test',
                    '--do-log']
        args = log_args + args

    args = ['--config-dir', '/tmp/isomer-test/etc/isomer'] + args

    pprint(args)

    runner = CliRunner()
    result = runner.invoke(cmd, args, catch_exceptions=False, obj={})
    with open('/tmp/logfile_runner', 'a') as f:
        f.write(result.output)
    return result
