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

Module: Misc
============

Miscellaneous functionality for the management tool.

"""

import click
from click_repl import repl
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from isomer.tool import run_process
from isomer.tool.cli import cli
from isomer.version import version_info


@cli.command(short_help="Start interactive management shell")
def shell():
    """Open an shell to work with the manage tool interactively."""

    print(
        """Isomer - Management Tool Interactive Prompt

    Type -h for help, tab completion is available, hit Ctrl-D to quit."""
    )

    style = Style.from_dict(
        {
            # User input (default text).
            "": "ansiwhite",
            "space": "ansigreen nounderline",
            "prompt": "ansicyan underline",
            "bottom-toolbar": "ansiblue",
            "bottom-toolbar-name": "bg:ansicyan",
        }
    )

    completer_styles = {
        "command": "ansicyan",
        "option": "ansigreen",
        "argument": "ansiyellow",
    }

    message = [("class:prompt", ">>"), ("class:space", " ")]

    def bottom_toolbar():
        """Returns a nice isomeric toolbar with the current version displayed"""
        return [
            ("class:bottom-toolbar-name", " Isomer "),
            ("class:bottom-toolbar", "maintenance tool (%s)" % version_info),
        ]

    prompt_kwargs = {
        "history": FileHistory("/tmp/.isomer-manage.history"),
        "message": message,
        "style": style,
        "bottom_toolbar": bottom_toolbar,
    }

    repl(
        click.get_current_context(),
        prompt_kwargs=prompt_kwargs,
        styles=completer_styles,
    )


@cli.command(short_help="View command map graph")
@click.option(
    "--xdot", help="Use xdot for nicer displaying", is_flag=True, default=False
)
def cmdmap(xdot):
    """Generates a command map"""
    # TODO: Integrate the output into documentation

    from copy import copy

    def generate_command_graph(command, map_output, groups=None, depth=0):
        """Generate a strict digraph (as indented representation) of all known
        subgroups and commands"""

        if groups is None:
            groups = []
        if "commands" in command.__dict__:
            if len(groups) > 0:
                if xdot:
                    line = '    "%s" -> "%s" [weight=1.0];\n' % (
                        groups[-1],
                        command.name,
                    )
                else:
                    line = "    " * (depth - 1) + "%s %s\n" % (groups[-1], command.name)
                map_output.append(line)

            for item in command.commands.values():
                subgroups = copy(groups)
                subgroups.append(command.name)
                generate_command_graph(item, map_output, subgroups, depth + 1)
        else:
            if xdot:
                line = '    "%s" -> "%s" [weight=%1.1f];\n' % (
                    groups[-1],
                    command.name,
                    len(groups),
                )
            else:
                line = "    " * (len(groups) - 3 + depth) + "%s %s\n" % (
                    groups[-1],
                    command.name,
                )
            map_output.append(line)

    output = []
    generate_command_graph(cli, output)

    output = [line.replace("cli", "isomer") for line in output]

    if xdot:
        with open("iso-tool.dot", "w") as f:
            f.write("strict digraph {\n")
            f.writelines(sorted(output))
            f.write("}")

        run_process(".", ["xdot", "iso-tool.dot"])
    else:
        print("".join(output))
