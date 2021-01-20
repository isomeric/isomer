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

Test Isomer Tools
===============



"""

# import os
import re

import pytest
import dateutil.parser
from tempfile import NamedTemporaryFile
from copy import copy
# from datetime import datetime

import isomer.tool.templates
from isomer.misc.std import std_table, std_uuid, std_now, std_color, std_hash, \
    std_salt, std_datetime, std_human_uid
from isomer.misc import path, nested_map_find, nested_map_update
from collections import namedtuple

template = """Hello {{placeholder}}!"""

content = {
    'placeholder': 'Isomer dev'
}

nested_map = {
    "app": {
        "Garden": {
            "Flowers": {
                "Red flower": "Rose",
                "White Flower": "Jasmine",
                "Yellow Flower": "Marigold"
            }
        },
        "Fruits": {
            "Yellow fruit": "Mango",
            "Green fruit": "Guava",
            "White Flower": "groovy"
        },
        "Trees": {
            "label": {
                "Yellow fruit": "Pumpkin",
                "White Flower": "Bogan"
            }
        }
    }
}

key = 'app.Garden.Flowers.White Flower'.split('.')


def test_uuid():
    uuid = std_uuid()

    assert isinstance(uuid, str)
    assert re.match(r'(\w{8}(-\w{4}){3}-\w{12}?)', uuid)

def test_std_salt():
    test_salt = std_salt()
    # b'$2b$12$CFbqPr4m0sE5OTvVVxTyWO'

    assert isinstance(test_salt, bytes) is True
    assert test_salt[0:7].decode('ascii') == '$2b$12$'


def test_std_now():
    now = std_now()

    assert isinstance(now, str)

    try:
        result = dateutil.parser.parse(now)
    except ValueError:
        pytest.fail('std_now produces non parsable datetime strings')


def test_std_table():
    Row = namedtuple("Row", ['A', 'B'])
    rows = [
        Row("1", "2")
    ]

    table = std_table(rows)

    rows.append(Row("345", "6"))
    table = std_table(rows)


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
    path.set_instance('TESTING', 'MAUVE', '/tmp/isomer-test')

    assert path.INSTANCE == 'TESTING'
    assert path.ENVIRONMENT == 'MAUVE'

    assert 'cache' in path.locations
    assert 'local' in path.locations
    assert 'lib' in path.locations

    assert path.get_path('cache',
                         '') == '/tmp/isomer-test/var/cache/isomer/TESTING/MAUVE'
    assert path.get_path('local',
                         'foo') == '/tmp/isomer-test/var/local/isomer/TESTING/MAUVE/foo'
    assert path.get_path('lib',
                         'bar/qux') == '/tmp/isomer-test/var/lib/isomer/TESTING/MAUVE/bar/qux'


def test_nested_map_find():
    """Tests if nested dictionaries can be traversed"""

    assert nested_map_find(nested_map, key) == 'Jasmine'


def test_nested_map_update():
    """Tests if nested dictionaries can be updated"""

    assert nested_map_find(
        nested_map_update(nested_map, 'Tulip', key),
        key) == 'Tulip'


def test_nested_map_delete():
    """Tests if nested dictionaries items can be deleted"""

    deletable_map = copy(nested_map)

    with pytest.raises(KeyError):
        nested_map_find(nested_map_update(deletable_map, None, key), key)
