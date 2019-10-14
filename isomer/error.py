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

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

"""


Module: Error
=============

Error handling


"""

import sys

EXIT_INVALID_ENVIRONMENT = {'code': 1, 'message': ''}
EXIT_INVALID_CONFIGURATION = {'code': 2, 'message': ''}
EXIT_INVALID_SOURCE = {'code': 3, 'message': ''}
EXIT_NO_PERMISSION = {'code': 5, 'message': ''}
EXIT_INSTALLATION_FAILED = {'code': 11, 'message': ''}
EXIT_PROVISIONING_FAILED = {'code': 12, 'message': ''}
EXIT_INSTANCE_EXISTS = {'code': 21, 'message': ''}
EXIT_INSTANCE_UNKNOWN = {'code': 22, 'message': ''}
EXIT_SERVICE_INVALID = {'code': 31, 'message': ''}
EXIT_USER_BAILED_OUT = {'code': 41, 'message': ''}
EXIT_NOTHING_TO_ARCHIVE = {'code': 51, 'message': ''}
EXIT_NO_CONFIGURATION = {'code': 61, 'message': ''}
EXIT_INVALID_PARAMETER = {'code': 62, 'message': ''}
EXIT_NO_CERTIFICATE = {'code': 63, 'message': ''}
EXIT_NO_DATABASE = {'code': 50020, 'message': ''}


def abort(error_object):
    if isinstance(error_object, int):
        print('Unknown error code.')
        sys.exit(error_object)
    else:
        print(error_object.get(
            'message',
            'Sorry, no error message for this specific problem found!'
        ))
        sys.exit(error_object['code'])
