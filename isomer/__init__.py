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

Package Isomer
==============

The backend package.

This is a namespace package.

"""
__all__ = [
    "events",
    "provisions",
    "schemata",
    "ui",
    "misc",
    "tool",
    "iso",
    "component",
    "database",
    "debugger",
    "launcher",
    "logger",
    "migration",
]

# See https://packaging.python.org/guides/packaging-namespace-packages/
# (Specifically the chapter on pkg_resources)
__import__("pkg_resources").declare_namespace(__name__)
