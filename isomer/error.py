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


Module: Error
=============

Error handling


"""

import sys

from isomer.logger import isolog, critical


def log(*args, **kwargs):
    """Log as previous emitter"""
    kwargs.update({"frame_ref": 2})
    kwargs["lvl"] = critical
    if "emitter" not in kwargs:
        kwargs["emitter"] = "MANAGE"
    isolog(*args, **kwargs)


# TODO:
#  * Categorize error codes into groups
#  * Enumerate codes
#  * Find all calls to abort and fix them up

INSTALL_MESSAGE = 'Please run "python3 setup.py install" first.\n' \
                  'If you get an error about setuptools, install python3 setuptools ' \
                  'for your distribution.\n\nFor more information, please read the ' \
                  'manual installation instructions:\n' \
                  'https://isomer.readthedocs.io/en/latest/start/installing.html#manual'

EXIT_INVALID_ENVIRONMENT = {"code": 1, "message": ""}
EXIT_INVALID_CONFIGURATION = {"code": 2, "message": ""}
EXIT_INVALID_INTERPRETER = {
    "code": 10,
    "message": "Invalid Python interpreter used. Isomer is not compatible with Python < 3.6!"
}
EXIT_CANNOT_IMPORT_INSTALLER = {"code": 11, "message": "Cannot import Isomer installer tool.\n" + INSTALL_MESSAGE}
EXIT_CANNOT_IMPORT_TOOL = {
    "code": 11,
    "message": "Cannot import Isomer tool.\nYou could inspect the problem by "
               "invoking the development tester:\n   python3 dev/isotest.py\n"
               "to get at the full error.\n\n" + INSTALL_MESSAGE
}
EXIT_NO_CONFIGURATION = {"code": 61, "message": ""}
EXIT_NOT_OVERWRITING_CONFIGURATION = {
    "code": 52,
    "message": "Configuration directory exists, not overwriting!",
}

EXIT_INVALID_SOURCE = {
    "code": 3,
    "message": "Only installing from github or local is currently supported",
}
EXIT_ROOT_REQUIRED = {"code": 4, "message": "Need root access to install. Use sudo."}
EXIT_NO_PERMISSION = {"code": 5, "message": "No permission. Maybe use sudo?"}
EXIT_FRONTEND_BUILD_FAILED = {"code": 6, "message": "Frontend was not built."}
EXIT_INSTALLATION_FAILED = {
    "code": 11,
    "message": "Installation failed. Check logs and/or increase logging via "
               "--clog/--flog",
}
EXIT_PROVISIONING_FAILED = {"code": 12, "message": "Could not provision required data."}
EXIT_INSTANCE_EXISTS = {"code": 21, "message": "Instance already exists"}
EXIT_INSTANCE_UNKNOWN = {"code": 22, "message": ""}
EXIT_SERVICE_INVALID = {"code": 31, "message": ""}
EXIT_USER_BAILED_OUT = {"code": 41, "message": ""}
EXIT_NOTHING_TO_ARCHIVE = {"code": 51, "message": ""}

EXIT_INVALID_PARAMETER = {
    "code": 62,
    "message": "Invalid instance configuration parameter specified",
}
EXIT_INVALID_VALUE = {
    "code": 64,
    "message": "Invalid instance configuration value specified",
}
EXIT_NO_CERTIFICATE = {"code": 63, "message": ""}
EXIT_NO_DATABASE = {"code": 50020, "message": "No database is available"}
EXIT_NO_DATABASE_DEFINED = {
    "code": 50021,
    "message": "No database name is defined for this instance - is it created already?"
}
EXIT_NO_DATABASE_HOST = {
    "code": 50021,
    "message": "Database host is not correctly defined. Check your command arguments or the configuration files."
}
EXIT_ISOMER_URL_REQUIRED = {
    "code": 50100,
    "message": "You need to specify a source url via --url/-u for isomer",
}
EXIT_STORE_PACKAGE_NOT_FOUND = {
    "code": 50404,
    "message": "The requested package is not available in the store",
}
EXIT_WORK_IN_PROGRESS = {"code": 55555, "message": "This is work in progress"}


def abort(error_object, ctx=None):
    """Abort with a nice error message and if possible an error description
    url leading to the online documentation."""

    if ctx is not None:
        parent = ctx.parent
        commands = ctx.info_name
        while parent is not None and parent.info_name is not None:
            commands = parent.info_name + " " + commands
            parent = parent.parent
        log("Abort:", commands)

    url = "https://isomer.readthedocs.io/en/latest/manual/Administration/Errors/%i.html"
    code = -1

    if isinstance(error_object, int):
        log("Unknown error code.")
        log(
            "You might be able to find more information above or here:",
            url % error_object,
        )
        code = error_object
    else:
        log(
            error_object.get(
                "message", "Sorry, no error message for this specific problem found."
            )
        )
        log(
            "Please see ",
            url % error_object.get("code", "no_code"),
            "for more information on this error.",
        )
        code = error_object["code"]

    if not ctx.obj.get('interactive', False):
        sys.exit(code)


def warn_error(error_object):
    """Warn with a nice error message and if possible an error description
    url leading to the online documentation."""

    url = "https://isomer.readthedocs.io/en/latest/manual/Administration/Errors/%i.html"
    if isinstance(error_object, int):
        log("Unknown error code.")
        log(
            "You might be able to find more information above or here:",
            url % error_object,
        )
    else:
        log(
            error_object.get(
                "message", "Sorry, no error message for this specific problem found."
            )
        )
        log(
            "Please see ",
            url % error_object.get("code", "no_code"),
            "for more information.",
        )
