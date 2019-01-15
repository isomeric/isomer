#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2018 Heiko 'riot' Weinen <riot@c-base.org> and others.
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

import getpass
import sys
import distro

import hashlib
import os

from isomer.logger import isolog, error, verbose, debug, warn
from isomer.tool.defaults import db_host_default, db_host_help, db_host_metavar, db_default, db_help, db_metavar, \
    platforms

try:
    import spur
except ImportError:
    import subprocess


    class spur_mock(object):
        def __init__(self):
            pass

        def LocalShell(self):
            return subprocess

    spur = spur_mock()


def log(*args, **kwargs):
    """Log as Emitter:MANAGE"""

    kwargs.update({'emitter': 'MANAGE', 'frame_ref': 2})
    isolog(*args, **kwargs)


def check_root():
    """Check if current user has root permissions"""

    if os.geteuid() != 0:
        log("Need root access to install. Use sudo!", lvl=error)
        log("If you installed into a virtual environment, don't forget to "
            "specify the interpreter binary for sudo, e.g:\n"
            "$ sudo /home/user/.virtualenv/isomer/bin/python3 iso")

        sys.exit(1)


def run_process(cwd, args, shell=None):
    """Executes an external process via subprocess.check_output"""

    log("Running:", cwd, args, lvl=verbose)

    if shell is None:
        log('Running on local shell', lvl=verbose)
        shell = spur.LocalShell()
    else:
        log('Running on remote shell:', shell, lvl=debug)

    try:
        process = shell.run(args, cwd=cwd)

        return True, process
    except spur.RunProcessError as e:
        log('Uh oh, the teapot broke again! Error:', e, type(e), lvl=verbose, pretty=True)
        log(e.args, e.return_code, e.output, lvl=verbose)
        return False, e
    except spur.NoSuchCommandError as e:
        log('Command was not found:', e, type(e), lvl=verbose, pretty=True)
        log(args)
        return False, e


def ask_password():
    """Securely and interactively ask for a password"""

    password = "Foo"
    password_trial = ""

    while password != password_trial:
        password = getpass.getpass()
        password_trial = getpass.getpass(prompt="Repeat:")
        if password != password_trial:
            print("\nPasswords do not match!")

    return password


def _get_credentials(username=None, password=None, dbhost=None):
    """Obtain user credentials by arguments or asking the user"""

    # Database salt
    system_config = dbhost.objectmodels['systemconfig'].find_one({
        'active': True
    })

    try:
        salt = system_config.salt.encode('ascii')
    except (KeyError, AttributeError):
        log('No systemconfig or it is without a salt! '
            'Reinstall the system provisioning with'
            'iso install provisions -p system')
        sys.exit(3)

    if username is None:
        username = ask("Please enter username: ")

    if password is None:
        password = ask_password()

    try:
        password = password.encode('utf-8')
    except UnicodeDecodeError:
        password = password

    passhash = hashlib.sha512(password)
    passhash.update(salt)

    return username, passhash.hexdigest()


def _get_system_configuration(dbhost, dbname):
    from isomer import database
    database.initialize(dbhost, dbname)
    systemconfig = database.objectmodels['systemconfig'].find_one({
        'active': True
    })

    return systemconfig


def ask(question, default=None, data_type='str', show_hint=False):
    """Interactively ask the user for data"""

    data = default

    if data_type == 'bool':
        data = None
        default_string = "Y" if default else "N"

        while data not in ('Y', 'J', 'N', '1', '0'):
            data = input("%s? [%s]: " % (question, default_string)).upper()

            if data == '':
                return default

        return data in ('Y', 'J', '1')
    elif data_type in ('str', 'unicode'):
        if show_hint:
            msg = "%s? [%s] (%s): " % (question, default, data_type)
        else:
            msg = question

        data = input(msg)

        if len(data) == 0:
            data = default
    elif data_type == 'int':
        if show_hint:
            msg = "%s? [%s] (%s): " % (question, default, data_type)
        else:
            msg = question

        data = input(msg)

        if len(data) == 0:
            data = int(default)
        else:
            data = int(data)
    else:
        print('Programming error! Datatype invalid!')

    return data


def format_result(result):
    return str(result.output).replace('\\n', '\n').replace('\\', '')


def get_isomer(source, url, destination, shell=None):
    """Grab a copy of Isomer somehow"""

    success = False

    if source == 'git':
        log('Cloning repository from', url)
        success, result = run_process(destination, ['git', 'clone', url, 'repository'], shell)
        if not success:
            log(result, lvl=error)
        log('Pulling frontend')
        success, result = run_process(os.path.join(destination, 'repository', 'frontend'), ['git', 'pull'], shell)
        if not success:
            log(result, lvl=error)
    elif source == 'link':
        if shell is not None:
            log('Remote Linking? Are you sure? Links will be local, they cannot span over any network.', lvl=warn)

        path = os.path.abspath(url)

        if not os.path.exists(os.path.join(destination, 'repository')):
            log('Linking repository from', path)
            success, result = run_process(destination, ['ln', '-s', path, 'repository'], shell)
            if not success:
                log(result, lvl=error)
        else:
            log('Repository already exists!', lvl=warn)

        if not os.path.exists(os.path.join(destination, 'repository', 'frontend', 'src')):
            log('Linking frontend')
            success, result = run_process(
                destination, ['ln', '-s', os.path.join(path, 'frontend'), 'repository/frontend'], shell
            )
            if not success:
                log(result, lvl=error)
        else:
            log('Frontend already present')
    elif source == 'copy':
        log('Copying local repository to remote.')

        path = os.path.realpath(os.path.expanduser(url))

        if shell is None:
            shell = spur.LocalShell()

        shell.upload_dir(path, destination, ['.tox*', 'node_modules*'])

    return success


def install_isomer(platform_name=None, use_sudo=False, shell=None, cwd='.', show=False):
    """Installs all dependencies"""

    if platform_name is None:
        platform_name = distro.linux_distribution()[0]
        log('Platform detected as %s' % platform_name)

    if isinstance(platforms[platform_name], str):
        platform_name = platforms[platform_name]
        log('This platform is a link to another:', platform_name, lvl=verbose)

    if platform_name not in platforms:
        log('Your platform is not yet officially supported!\n\n'
            'Please check the documentation for more information:\n'
            'https://isomer.readthedocs.io/en/latest/start/platforms/support.html', lvl=error)
        sys.exit(50000)

    if shell is None and use_sudo is False:
        check_root()

    def build_command(*things):
        """Construct a command adding sudo if necessary"""
        if use_sudo:
            cmd = ['sudo']
        else:
            cmd = []

        for thing in things:
            cmd += [thing]

        return cmd

    def platform():
        """In a platform specific way, install all dependencies"""

        tool = platforms[platform_name]['tool']
        packages = platforms[platform_name]['packages']
        pre_install_commands = platforms[platform_name]['pre_install']
        post_install_commands = platforms[platform_name]['post_install']

        for command in pre_install_commands:
            args = build_command(*command)
            log('Running pre install command')
            if show:
                log(args)
            success, output = run_process(cwd, args, shell)
            if not success:
                log('Could not run command %s!' % command, lvl=error)
                log(args, output, pretty=True)

        log('Installing platform dependencies')
        args = build_command(*tool + packages)
        if show:
            log(args)
        success, output = run_process(cwd, args, shell)
        if not success:
            log('Could not install %s dependencies!' % platform, lvl=error)
            log(args, output, pretty=True)

        for command in post_install_commands:
            args = build_command(*command)
            log('Running command')
            if show:
                log(args)
            success, output = run_process(cwd, args, shell)
            if not success:
                log('Could not run command %s!' % command, lvl=error)
                log(args, output, pretty=True)

    def common():
        """Perform platform independent setup"""

        log('Installing Isomer')
        args = build_command('python3', 'setup.py', 'develop')
        if show:
            log(args)
        success, output = run_process(cwd, args, shell)
        if not success:
            log('Could not install Isomer package!', lvl=error)
            log(args, output, pretty=True)

        log('Installing Isomer requirements')
        args = build_command('pip3', 'install', '-r', 'requirements.txt')
        if show:
            log(args)
        success, output = run_process(cwd, args, shell)
        if not success:
            log('Could not install Python dependencies!', lvl=error)
            log(args, output, pretty=True)

    platform()
    common()
