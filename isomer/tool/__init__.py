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


"""

Package: Tool
=============

Contains basic functionality for the isomer management tool.


Command groups
--------------

backup
configuration
create_module
database
defaults
dev
environment
etc
installer
instance
misc
objects
rbac
remote
system
user

General binding glue
--------------------

cli
templates
tool


"""

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import getpass
import sys
import distro

import hashlib
import os

from tomlkit.exceptions import NonExistentKey

from isomer.logger import isolog, verbose, debug, error, warn
from isomer.tool.defaults import db_host_default, db_host_help, db_host_metavar, db_default, db_help, db_metavar, \
    platforms, EXIT_INVALID_CONFIGURATION, EXIT_INSTANCE_UNKNOWN

try:
    import spur
except ImportError:
    import subprocess


    class spur_mock(object):
        """Mock object for cases where spur was not installed."""

        @staticmethod
        def LocalShell():
            """Only defines a local shell which behaves like a standard library subprocess"""
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

        sys.exit(50001)


def run_process(cwd, args, shell=None, sudo=None, show=False):
    """Executes an external process via subprocess.check_output"""

    log("Running:", cwd, args, lvl=verbose)

    # if shell is None and sudo is None:
    #     check_root()

    def build_command(*things):
        """Construct a command adding sudo if necessary"""

        if sudo not in (None, False, 'False'):
            if isinstance(sudo, bool) and sudo is True or sudo == 'True':
                user = 'root'
            elif isinstance(sudo, str):
                user = sudo
            else:
                log('Malformed run_process call:', things, lvl=error)
                return

            log('Using sudo with user:', user, lvl=verbose)
            cmd = ['sudo', '-u', user] + list(things)
        else:
            log('Not using sudo', lvl=verbose)
            cmd = []
            for thing in things:
                cmd += [thing]

        return cmd

    if shell is None:
        log('Running on local shell', lvl=verbose)
        shell = spur.LocalShell()
    else:
        log('Running on remote shell:', shell, lvl=debug)

    command = build_command(*args)
    log(command, lvl=verbose)

    try:
        if show:
            log('Executing:', command)
        process = shell.run(command, cwd=cwd)

        log(process.output, lvl=verbose)

        return True, process
    except spur.RunProcessError as e:
        log('Uh oh, the teapot broke again! Error:', e, type(e), lvl=verbose, pretty=True)
        log(command, e.args, e.return_code, e.output, lvl=verbose)
        if e.stderr_output not in ("", None, False):
            log('Error output:', e.stderr_output, lvl=error)
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
    """Format child instance output"""
    return str(result.output, encoding='ascii').replace('\\n', '\n')


def get_isomer(source, url, destination, upgrade=False, shell=None, sudo=None):
    """Grab a copy of Isomer somehow"""
    success = False

    if source == 'git':
        if not upgrade:
            log('Cloning repository from', url)
            success, result = run_process(destination, ['git', 'clone', url, 'repository'], shell, sudo)
            if not success:
                log(result, lvl=error)
                sys.exit(50000)
        else:
            log('Updating repository from', url)
            success, result = run_process(os.path.join(destination, 'repository'),
                                          ['git', 'pull', 'origin', 'master'], shell, sudo)
            if not success:
                log(result, lvl=error)
                sys.exit(50000)

        repository = os.path.join(destination, 'repository')
        log('Initializing submodules')
        success, result = run_process(repository, ['git', 'submodule', 'init'], shell, sudo)
        if not success:
            log(result, lvl=error)
            sys.exit(50000)
        success, result = run_process(repository, ['git', 'submodule', 'update'], shell, sudo)
        if not success:
            log(result, lvl=error)
            sys.exit(50000)

        log('Pulling frontend')
        success, result = run_process(os.path.join(repository, 'frontend'),
                                      ['git', 'pull', 'origin', 'master'], shell, sudo)
        if not success:
            log(result, lvl=error)
            sys.exit(50000)
    elif source == 'link':
        if shell is not None:
            log('Remote Linking? Are you sure? Links will be local, they cannot span over any network.', lvl=warn)

        path = os.path.abspath(url)

        if not os.path.exists(os.path.join(destination, 'repository')):
            log('Linking repository from', path)
            success, result = run_process(destination, ['ln', '-s', path, 'repository'], shell, sudo)
            if not success:
                log(result, lvl=error)
                sys.exit(50000)
        else:
            log('Repository already exists!', lvl=warn)

        if not os.path.exists(os.path.join(destination, 'repository', 'frontend', 'src')):
            log('Linking frontend')
            success, result = run_process(
                destination, ['ln', '-s', os.path.join(path, 'frontend'), 'repository/frontend'], shell, sudo
            )
            if not success:
                log(result, lvl=error)
                sys.exit(50000)
        else:
            log('Frontend already present')
    elif source == 'copy':
        log('Copying local repository')

        path = os.path.realpath(os.path.expanduser(url))
        target = os.path.join(destination, 'repository')

        if shell is None:
            shell = spur.LocalShell()
        else:
            log('Copying to remote')

        log('Copying %s to %s' % (path, target), lvl=verbose)

        shell.upload_dir(path, target, ['.tox*', 'node_modules*'])

        if sudo is not None:
            success, result = run_process(
                '/', ['chown', sudo, '-R', target]
            )
            if not success:
                log('Could not change ownership to', sudo, lvl=warn)
                sys.exit(50000)
        return True

    return success


def install_isomer(platform_name=None, use_sudo=False, shell=None, cwd='.',
                   show=False, omit_common=False, omit_platform=False):
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

    def platform():
        """In a platform specific way, install all dependencies"""

        tool = platforms[platform_name]['tool']
        packages = platforms[platform_name]['packages']
        pre_install_commands = platforms[platform_name]['pre_install']
        post_install_commands = platforms[platform_name]['post_install']

        for command in pre_install_commands:
            log('Running pre install command', " ".join(command))
            success, output = run_process(cwd, command, shell, sudo=use_sudo)
            if not success:
                log('Could not run command %s!' % command, lvl=error)
                log(output, pretty=True)

        log('Installing platform dependencies')
        success, output = run_process(cwd, tool + packages, shell, sudo=use_sudo)
        if not success:
            log('Could not install %s dependencies!' % platform_name, lvl=error)
            log(output, pretty=True)

        for command in post_install_commands:
            log('Running post install command')
            success, output = run_process(cwd, command, shell, sudo=use_sudo)
            if not success:
                log('Could not run command %s!' % command, lvl=error)
                log(output, pretty=True)

    def common():
        """Perform platform independent setup"""

        log('Installing Isomer')
        success, output = run_process(cwd, ['python3', 'setup.py', 'develop'], shell, sudo=use_sudo)
        if not success:
            log('Could not install Isomer package!', lvl=error)
            log(output, pretty=True)

        log('Installing Isomer requirements')

        success, output = run_process(cwd, ['pip3', 'install', '-r', 'requirements.txt'], shell, sudo=use_sudo)
        if not success:
            log('Could not install Python dependencies!', lvl=error)
            log(output, pretty=True)

    if not omit_platform:
        platform()

    if not omit_common:
        common()


def _get_configuration(ctx):
    try:
        log('Configuration:', ctx.obj['config'], lvl=verbose, pretty=True)
        log('Instance:', ctx.obj['instance'], lvl=debug)
    except KeyError:
        log('Invalid configuration, stopping.', lvl=error)
        sys.exit(EXIT_INVALID_CONFIGURATION)

    try:
        instance_configuration = ctx.obj['instances'][ctx.obj['instance']]
        log('Instance Configuration:', instance_configuration, lvl=verbose, pretty=True)
    except NonExistentKey:
        log('Instance %s does not exist' % ctx.obj['instance'], lvl=warn)
        sys.exit(EXIT_INSTANCE_UNKNOWN)

    environment_name = instance_configuration['environment']
    environment_config = instance_configuration['environments'][environment_name]

    ctx.obj['environment'] = environment_config

    ctx.obj['instance_configuration'] = instance_configuration


def get_next_environment(ctx):
    """Return the next environment"""

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
    else:
        current_environment = ctx.obj['instance_configuration']['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'

    return next_environment
