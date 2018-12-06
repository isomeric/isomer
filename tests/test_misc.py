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
import isomer.tool.templates

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""
Hackerfleet Operating System - Backend

Test Isomer Tools
===============



"""

# import os
import re
import pytest
from tempfile import NamedTemporaryFile
# from datetime import datetime
import dateutil.parser

from isomer import misc
from isomer.misc import path
from collections import namedtuple

template = """Hello {{placeholder}}!"""

content = {
    'placeholder': 'Isomer dev'
}


def test_uuid():
    uuid = misc.std_uuid()

    assert isinstance(uuid, str)
    assert re.match('(\w{8}(-\w{4}){3}-\w{12}?)', uuid)


def test_std_now():
    now = misc.std_now()

    assert isinstance(now, str)

    try:
        result = dateutil.parser.parse(now)
    except ValueError:
        pytest.fail('std_now produces nom parsable datetime strings')


def test_std_table():
    Row = namedtuple("Row", ['A', 'B'])
    rows = [
        Row("1", "2")
    ]

    table = misc.std_table(rows)

    rows.append(Row("345", "6"))
    table = misc.std_table(rows)


def test_format_template():
    result = isomer.tool.templates.format_template(template, content)

    assert result == 'Hello Isomer dev!'


def test_format_template_file():
    with NamedTemporaryFile(prefix='isomer-test',
                            suffix='tpl',
                            delete=True) as f:
        f.write(template.encode('utf-8'))
        f.flush()
        result = isomer.tool.templates.format_template_file(f.name, content)

    assert result == 'Hello Isomer dev!'


def test_write_template_file():
    with NamedTemporaryFile(prefix='isomer-test',
                            suffix='tpl',
                            delete=True) as f:
        f.write(template.encode('utf-8'))
        f.flush()

        target = f.name + '_filled'
        isomer.tool.templates.write_template_file(f.name, target, content)

        with open(target, 'r') as tf:
            result = tf.readline()

        assert result == 'Hello Isomer dev!'

        print(target)


def test_path_tools():
    path.set_instance('TESTING', 'MAUVE')

    assert path.INSTANCE == 'TESTING'
    assert path.ENVIRONMENT == 'MAUVE'

    assert 'cache' in path.locations
    assert 'local' in path.locations
    assert 'lib' in path.locations

    assert path.get_path('cache', '') == '/tmp/isomer-test/var/cache/isomer/TESTING/MAUVE'
    assert path.get_path('local', 'foo') == '/tmp/isomer-test/var/local/isomer/TESTING/MAUVE/foo'
    assert path.get_path('lib', 'bar/qux') == '/tmp/isomer-test/var/lib/isomer/TESTING/MAUVE/bar/qux'
