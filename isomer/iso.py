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

from isomer.error import abort

if sys.version_info.major < 3:
    print(
        "The iso tool has been evoked with an older Python version. "
        "Please restart the iso tool in a valid environment."
    )
    abort(50053)

if not sys.warnoptions:

    def warn(*args, **kwargs):
        pass

    warnings.warn = warn

    warnings.simplefilter("ignore")

try:
    from isomer.tool import install_isomer, ask
except ImportError as e:
    # TODO: Make sure weird, pre install dependencies are mentioned:
    # build-essentials
    # python3-dev
    # python3-cffi, libffi-dev, libssl-dev (for spur)
    # python3-pip
    print("Cannot run iso-tool:", e, type(e))
    print(
        'Please run "python3 setup.py install" first.\n'
        "If you get an error about setuptools, install python3 setuptools for your distribution.\n\n"
        "For more information, please read the manual installation instructions:\n"
        "https://isomer.readthedocs.io/en/latest/start/installing.html#manual"
    )
    abort(50050)


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
        print(type(import_exception), ":", import_exception)
        if not ask(
            "Dependencies not installed, do you want to try to install them",
            default=False,
            data_type="bool",
            show_hint=True,
        ):
            abort(50051)

        install_isomer()
        print("Please restart the tool")
        sys.exit()

    isotool(obj={}, auto_envvar_prefix="ISOMER")


if __name__ == "__main__":
    main()
