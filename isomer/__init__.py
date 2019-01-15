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


"""

Package ISOMER
==============

The backend package.

This is a namespace package.

:copyright: (C) 2011-2018 riot@c-base.org
:license: AGPLv3 (See LICENSE)

"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"
__all__ = ['events', 'provisions', 'schemata', 'ui', 'misc', 'tool', 'iso',
           'component', 'database', 'debugger', 'launcher', 'logger', 'migration']

# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:  # pragma: no cover
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:  # pragma: no cover

    from pkgutil import extend_path

    __path__ = extend_path(__path__, __name__)  # noqa
    import os

    for _path in __path__:
        _path = os.path.join(_path, '__init__.py')
        if _path != __file__ and os.path.exists(_path):
            with open(_path) as fd:
                exec(fd, globals())

    del os, extend_path, _path
