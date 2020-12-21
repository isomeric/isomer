#!/usr/bin/env python3
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

Isomer Management Tool
======================

This is the management tool to install, configure and maintain
Isomer instances.

"""

import sys
import warnings

from isomer.error import abort, EXIT_INVALID_INTERPRETER, EXIT_CANNOT_IMPORT_INSTALLER, \
    EXIT_CANNOT_IMPORT_TOOL

if sys.version_info.major < 3:
    abort(EXIT_INVALID_INTERPRETER)

if not sys.warnoptions:
    def warn(*args, **kwargs):
        pass


    warnings.warn = warn

    warnings.simplefilter("ignore")

try:
    # noinspection PyUnresolvedReferences
    from isomer.tool import install_isomer, ask
except ImportError as e:
    # TODO: Make sure weird, pre install dependencies are mentioned:
    # build-essentials
    # python3-dev
    # python3-cffi, libffi-dev, libssl-dev (for spur)
    # python3-pip
    print("\033[1;33;41mCannot run iso-tool:", e, type(e), "\033[0m")
    abort(EXIT_CANNOT_IMPORT_INSTALLER)


# TODO: Document zsh/bash autocompletion for iso tool
# https://click.palletsprojects.com/en/7.x/bashcomplete/#completion-help-strings-zsh-only
# zsh:  eval "$(_ISO_COMPLETE=source_zsh iso)"
# bash: eval "$(_ISO_COMPLETE=source iso)"


def main():
    """Try to load the tool and launch it. If it can't be loaded, try to install
    all required things first."""

    try:
        from isomer.tool.tool import isotool
    except ImportError as import_exception:
        print(
            "\033[1;33;41mIsomer startup error! Please check your Isomer/Python installation.\033[0m")
        print(type(import_exception), ":", import_exception, "\n")

        if not ask(
                "Maybe the dependencies not installed, do you want to try to install them",
                default=False,
                data_type="bool",
                show_hint=True,
        ):
            abort(EXIT_CANNOT_IMPORT_TOOL)

        install_isomer()
        print("Please restart the tool now.")
        sys.exit()

    isotool(obj={}, auto_envvar_prefix="ISOMER")


if __name__ == "__main__":
    main()
