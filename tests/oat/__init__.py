import os
import shutil
from pprint import pprint

from click.testing import CliRunner
from isomer.misc.path import set_etc_path, set_instance

colors = False


def reset_base():
    """Prepares a testing folder and sets Isomer's base to that"""
    if os.path.exists('/tmp/isomer-test'):
        shutil.rmtree('/tmp/isomer-test')

    os.makedirs('/tmp/isomer-test/etc/isomer/instances')
    os.makedirs('/tmp/isomer-test/var/log/isomer')

    set_etc_path('/tmp/isomer-test/etc/isomer')
    set_instance('foobar', 'green', '/tmp/isomer-test/')


def run_cli(cmd, args, full_log=False):
    """Runs a command"""

    if colors is False:
        args.insert(0, '-nc')

    if full_log:
        log_args = ['--clog', '5', '--flog', '5', '--log-path', '/tmp/isomer-test',
                    '--do-log']
        args = log_args + args

    args = ['--config-dir', '/tmp/isomer-test/etc/isomer'] + args

    pprint(args)

    runner = CliRunner()
    result = runner.invoke(cmd, args, catch_exceptions=False, obj={})
    with open('/tmp/logfile_runner', 'a') as f:
        f.write(result.output)
    return result
