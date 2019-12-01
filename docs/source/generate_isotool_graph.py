#!/usr/bin/env python

import os
from isomer.tool.tool import isotool
from copy import copy


def write_command_map(filename=None):
    """Write the iso-tool command map to the source folder"""

    def assemble_commands(command, output, groups=[], level=0):
        """Recursively generate a dot-graph of the iso-tool"""
        if level >= 2:
            return
        if 'commands' in command.__dict__:
            if len(groups) > 0:
                line = '    "%s" -> "%s" [weight=1.0];\n' % \
                       (groups[-1], command.name)
                line = line.replace('"cli"', '"isotool"')
                output.append(line)

            for item in command.commands.values():
                subgroups = copy(groups)
                subgroups.append(command.name)
                assemble_commands(item, output, subgroups, level + 1)
        else:
            line = '    "%s" -> "%s" [weight=%1.1f];\n' % \
                   (groups[-1], command.name, len(groups))
            line = line.replace('"cli"', '"isotool"')
            output.append(line)

    if filename is None:
        filename = os.path.join(
            os.path.dirname(__file__),
            'manual/Administration/iso.dot'
        )
    with open(filename, 'w') as f:
        f.write('strict digraph {\n')
        output = []
        assemble_commands(isotool, output)
        f.writelines(sorted(output))
        f.write('}')


if __name__ == '__main__':
    write_command_map()
