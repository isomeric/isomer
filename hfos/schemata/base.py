#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HFOS - Hackerfleet Operating System
# ===================================
# Copyright (C) 2011-2017 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Heiko 'riot' Weinen"
__license__ = "GPLv3"

"""

Schema: User
============

Account credentials and administrativa

Contains
--------

User: Useraccount object


"""
from hfos.schemata.defaultform import noform


def base_object(name,
                has_owner=True,
                has_uuid=True,
                roles_write=None,
                roles_read=None,
                roles_list=None,
                roles_create=None,
                all_roles=None):
    if all_roles:
        roles_create = ['admin', all_roles]
        roles_write = ['admin', all_roles]
        roles_read = ['admin', all_roles]
        roles_list = ['admin', all_roles]
    else:
        if roles_write is None:
            roles_write = ['admin']
        if roles_read is None:
            roles_read = ['admin']
        if roles_list is None:
            roles_list = ['admin']
        if roles_create is None:
            roles_create = ['admin']

    if has_owner:
        roles_write.append('owner')
        roles_read.append('owner')
        roles_list.append('owner')

    base_schema = {
        'id': '#' + name,
        'type': 'object',
        'name': name,
        'roles_create': roles_create,
        'properties': {
            'perms': {
                'id': '#perms',
                'type': 'object',
                'name': 'perms',
                'properties': {
                    'write': {
                        'type': 'array',
                        'default': roles_write,
                        'items': {
                            'type': 'string',
                        }
                    },
                    'read': {
                        'type': 'array',
                        'default': roles_read,
                        'items': {
                            'type': 'string',
                        }
                    },
                    'list': {
                        'type': 'array',
                        'default': roles_list,
                        'items': {
                            'type': 'string',
                        }
                    }
                },
                'default': {},
                'x-schema-form': {
                    'condition': "false"
                }
            },
            'name': {
                'type': 'string'
            },
        },
    }

    if has_uuid:
        base_schema['properties'].update({
            'uuid': {
                'pattern': '^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-['
                           'a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
                'type': 'string',
                'title': 'Unique ' + name + ' ID',
                'x-schema-form': {
                    'condition': "false"
                }
            }
        })
        base_schema['required'] = ["uuid"]

    if has_owner:
        base_schema['properties'].update({
            'owner': {
                'pattern': '^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-['
                           'a-fA-F0-9]{4}-[a-fA-F0-9]{12}$',
                'type': 'string',
                'title': 'Unique Owner ID',
                'x-schema-form': {
                    'condition': "false"
                }
            }
        })
        # TODO: Schema should allow specification of non-local owners as well
        # as special accounts like admin or even system perhaps
        # base_schema['required'] = base_schema.get('required', [])
        # base_schema['required'].append('owner')

    return base_schema