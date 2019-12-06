#!/usr/bin/env python

import os
from isomer import error
from isomer.logger import isolog
from isomer.tool.templates import write_template_file

import inspect

TEMPLATE_FILE = '_templates/errors.rst'
ERROR_OUTPUT = os.path.join(
    os.path.dirname(__file__),
    'manual', 'Administration', 'Errors'
)


def get_errors():
    result = []

    for item in inspect.getmembers(error):
        if str(item[0]).startswith('EXIT'):
            result.append(item)

    return result


def write_errors(errors):
    for error in errors:
        content = error[1]
        code = content['code']
        msg = content['message']
        isolog('Creating Error %i: %s' % (code, msg))
        filename = os.path.join(ERROR_OUTPUT, "E%i.rst" % code)

        write_template_file(TEMPLATE_FILE, filename, content)


if __name__ == '__main__':
    write_errors(get_errors())
