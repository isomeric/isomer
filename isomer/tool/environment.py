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
import grp
import os
import pwd
import shutil
import sys
import tarfile
import click

from tempfile import mkdtemp
from click_didyoumean import DYMGroup
from git import Repo, exc

from isomer.scm_version import version
from isomer.database import initialize, backup, internal_restore
from isomer.logger import error, verbose, warn, critical, debug
from isomer.misc import std_uuid, std_now
from isomer.misc.path import set_instance, get_path, get_etc_path, locations, get_log_path, get_etc_instance_path
from isomer.tool import log, run_process, format_result, get_isomer, _get_configuration, get_next_environment
from isomer.tool.database import delete_database
from isomer.tool.defaults import EXIT_INVALID_SOURCE, source_url
from isomer.tool.etc import write_instance, environment_template

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"


@click.group(cls=DYMGroup)
@click.pass_context
def environment(ctx):
    """[GROUP] Various aspects of Isomer environment handling"""

    _get_configuration(ctx)


def _test_environment(ctx):
    """General fitness tests of the built environment"""
    # TODO: Implement environment testing
    log('Would now test the environment (Not implemented, yet)')
    return True


@environment.command(name='clear', short_help='Clear an environment')
@click.option('--force', '-f', is_flag=True, default=False)
@click.option('--no-archive', '-n', is_flag=True, default=False)
@click.pass_context
def clear_environment(ctx, force, no_archive):
    """Clear the non-active environment"""

    _clear_environment(ctx, force, no_archive=no_archive)


def _clear_environment(ctx, force=False, clear_env=None, no_archive=False):
    """Tests an environment for usage, then clears it"""

    instance_name = ctx.obj['instance']

    if clear_env is None:
        next_environment = get_next_environment(ctx)
    else:
        next_environment = clear_env

    log('Clearing environment:', next_environment)
    set_instance(instance_name, next_environment)

    # log('Testing', environment, 'for usage')

    env = ctx.obj['instance_config']['environments'][next_environment]

    if not no_archive:
        if not (_archive(ctx, force) or force):
            log('Archival failed, stopping.')
            sys.exit(5000)

    log('Clearing env:', env)

    for item in locations:
        path = get_path(item, '')
        log('Clearing [%s]: %s' % (item, path))
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            log('Path not found:', path, lvl=warn)
        except PermissionError:
            log('No permission to clear environment', lvl=error)
            return False

    _create_folders(ctx)

    delete_database(ctx.obj['dbhost'], '%s_%s' % (instance_name, next_environment), force=True)

    ctx.obj['instance_config']['environments'][next_environment] = environment_template
    write_instance(ctx.obj['instance_config'])
    return True


def _create_folders(ctx):
    """Generate required folders for an instance"""

    log("Generating instance directories", emitter='MANAGE')

    instance_config = ctx.obj['instance_config']

    try:
        uid = pwd.getpwnam(instance_config['user']).pw_uid
        gid = grp.getgrnam(instance_config['group']).gr_gid
    except KeyError:
        log('User account for instance not found!', lvl=warn)
        uid = gid = None

    logfile = os.path.join(get_log_path(), "isomer." + ctx.obj['instance'] + ".log")

    for item in locations:
        path = get_path(item, '', ensure=True)

        log("Created path: " + path)
        if os.geteuid() == 0 and uid is not None:
            os.chown(path, uid, gid)
        else:
            log('No root access - could not change ownership:', path, lvl=warn)

    module_path = get_path('lib', 'modules', ensure=True)
    if os.geteuid() == 0 and uid is not None:
        os.chown(module_path, uid, gid)
    else:
        log('No root access - could not change ownership:', module_path, lvl=warn)

    log('Module storage created:', module_path)

    if not os.path.exists(logfile):
        open(logfile, "w").close()

    if os.geteuid() == 0 and uid is not None:
        os.chown(logfile, uid, gid)
    else:
        log('No root access - could not change ownership', lvl=warn)

    log("Done: Create instance folders")


@environment.command(short_help="Archive the other environment")
@click.option('--force', '-f', is_flag=True, default=False)
@click.pass_context
def archive(ctx, force):
    """Archive the non-active  environment"""

    _archive(ctx, force)


def _archive(ctx, force=False):
    instance_config = ctx.obj['instance_config']

    next_environment = get_next_environment(ctx)

    env = instance_config['environments'][next_environment]

    log(instance_config, next_environment, pretty=True)
    log(env['installed'], env['tested'])
    if (not env['installed'] or not env['tested']) and not force:
        log('Environment has not been installed - not archiving.', lvl=warn)
        return False

    log('Archiving environment:', next_environment)
    set_instance(ctx.obj['instance'], next_environment)

    timestamp = std_now().replace(':', '-').replace('.', '-')

    temp_path = mkdtemp(prefix='isomer_backup')

    log('Archiving database')
    database_host = '%s:%i' % (instance_config['database_host'], instance_config['database_port'])
    if initialize(database_host, env['database'], ignore_fail=force):
        backup(None, None, None, 'json', os.path.join(temp_path, 'db_' + timestamp + '.json'), True, True, [])
    elif not force:
        log('Could not archive database.')
        return False

    try:
        archive_filename = os.path.join(
            '/var/backups/isomer/',
            '%s_%s_%s.tgz' % (ctx.obj['instance'], next_environment, timestamp)
        )

        shutil.copy(
            os.path.join(get_etc_instance_path(), ctx.obj['instance'] + '.conf'),
            temp_path
        )

        with tarfile.open(archive_filename, 'w:gz') as f:
            for item in locations:
                path = get_path(item, '')
                log('Archiving [%s]: %s' % (item, path))
                f.add(path)
            f.add(temp_path, 'db_etc')
    except (PermissionError, FileNotFoundError) as e:
        log('Could not archive environment:', e, lvl=error)
        if not force:
            return False
    finally:
        log('Clearing temporary backup target')
        shutil.rmtree(temp_path)

    ctx.obj['instance_config']['environments']['archive'][timestamp] = env

    log(ctx.obj['instance_config'])

    return True

    # TODO: confirm archival


@environment.command(short_help='Install frontend')
@click.pass_context
def install_frontend(ctx):
    """Foo"""

    next_environment = get_next_environment(ctx)

    set_instance(ctx.obj['instance'], next_environment)
    _install_frontend(ctx)


def _install_frontend(ctx):
    """Install and build the frontend"""

    env = get_next_environment(ctx)
    env_path = get_path('lib', '')

    instance_config = ctx.obj['instance_config']

    user = instance_config['user']

    log('Building frontend')

    success, result = run_process(
        os.path.join(env_path, 'repository'),
        [
            os.path.join(env_path, 'venv', 'bin', 'python3'),
            './iso', '-nc', '--config-dir', get_etc_path(), '-i', instance_config['name'], '-e', env,
            'install', 'frontend', '--rebuild'
        ],
        sudo=user
    )
    if not success:
        log(format_result(result), lvl=error)
        return False

    return True


@environment.command('install-module', short_help="Install a module into an environment")
@click.option('--source', '-s', default='git', type=click.Choice(['link', 'copy', 'git']))
@click.option('--force', '-f', default=False, is_flag=True, help='Force installation (overwrites old modules)')
@click.argument('url')
@click.pass_context
def install_environment_module(ctx, source, force, url):
    """Add and install a module"""

    instance_name = ctx.obj['instance']
    instance_configuration = ctx.obj['instances'][instance_name]

    next_environment = get_next_environment(ctx)
    user = instance_configuration['user']

    set_instance(instance_name, next_environment)

    result = _install_module(source, url, force, user)

    if result is False:
        log('Installation failed!', lvl=error)
        sys.exit(50000)

    package_name, package_version = result

    descriptor = [package_name, package_version, source, url]
    instance_configuration['environments'][next_environment]['modules'].append(descriptor)

    write_instance(instance_configuration)

    log('Done: Install environment module')


def _install_module(source, url, force=False, user=None):
    """Actually installs a module into an environment"""

    module_path = get_path('lib', 'modules', ensure=True)

    if source not in ('git', 'link', 'copy'):
        log('Only installing from github or local is currently supported', lvl=error)
        sys.exit(EXIT_INVALID_SOURCE)

    uuid = std_uuid()
    temporary_path = os.path.join(module_path, '%s' % uuid)

    log('Installing module: %s [%s]' % (url, source))

    if source == 'git':
        log('Cloning repository from', url)
        success, output = run_process(
            module_path, ['git', 'clone', url, temporary_path], sudo=user
        )
        if not success:
            log('Error:', output, lvl=error)
    elif source == 'link':
        log('Linking repository from', url)
        success, output = run_process(
            module_path, ['ln', '-s', url, temporary_path], sudo=user
        )
        if not success:
            log('Error:', output, lvl=error)
    elif source == 'copy':
        log('Linking repository from', url)
        success, output = run_process(
            module_path, ['cp', '-a', url, temporary_path], sudo=user
        )
        if not success:
            log('Error:', output, lvl=error)

    log('Getting name')
    success, result = run_process(
        temporary_path, ['python', 'setup.py', '--name'], sudo=user
    )
    if not success:
        log(format_result(result), pretty=True, lvl=error)
        return False

    package_name = str(result.output, encoding='utf8').rstrip('\n')

    log('Getting version')
    success, result = run_process(
        temporary_path, ['python', 'setup.py', '--version'], sudo=user
    )
    if not success:
        log(format_result(result), pretty=True, lvl=error)
        return False

    package_version = str(result.output, encoding='utf8').rstrip('\n')

    log('Package name:', package_name, 'version:', package_version)

    final_path = os.path.join(module_path, package_name)

    if os.path.exists(final_path):
        log('Module exists.', lvl=warn)
        if force:
            log('Removing previous version.')
            success, result = run_process(module_path, ['rm', '-rf', final_path], sudo=user)
            if not success:
                log('Could not remove previous version!', lvl=error)
                sys.exit(50000)
        else:
            log('Not overwriting previous version without --force', lvl=error)
            sys.exit(50000)

    log('Renaming to', final_path)
    os.rename(temporary_path, final_path)

    log('Installing module')
    success, output = run_process(
        final_path,
        [os.path.join(get_path('lib', 'venv'), 'bin', 'python3'), 'setup.py', 'develop'],
        sudo=user
    )
    if not success:
        log(output, lvl=verbose)
        return False
    else:
        return package_name, package_version


def _install_modules(ctx):
    """Install all given modules"""

    env = get_next_environment(ctx)
    log('Installing modules into', env, pretty=True)

    modules = ctx.obj['instance_config']['modules']
    user = ctx.obj['instance_config']['user']

    log(modules, pretty=True)

    for module in modules:
        log(module, pretty=True)
        _install_module(module['source'], module['url'], user)

    # TODO: Confirm in environment configuration which modules are installed

    return True


@environment.command(short_help='Install provisions and/or a database backup')
@click.option('--import-file', '--import', default=None, help='Import the specified backup')
@click.option('--skip-provisions', is_flag=True, default=False)
@click.pass_context
def install_provisions(ctx, import_file, skip_provisions):
    """Install provisions and/or a database dump"""
    _install_provisions(ctx, import_file, skip_provisions)


def _install_provisions(ctx, import_file=None, skip_provisions=False):
    """Load provisions into database"""

    instance_config = ctx.obj['instance_config']
    env = get_next_environment(ctx)
    env_path = get_path('lib', '')

    log('Installing provisioning data')

    # TODO: Dependencies of provisions!
    # First, user has to be provisioned, then system, then the rest

    if not skip_provisions:
        success, result = run_process(
            os.path.join(env_path, 'repository'),
            [
                os.path.join(env_path, 'venv', 'bin', 'python3'),
                './iso', '-nc', '--clog', '5', '--config-dir', get_etc_path(), '-i', instance_config['name'], '-e', env,
                'install', 'provisions'
            ]  # Note: no sudo necessary as long as we do not enforce authentication on databases
        )
        if not success:
            log('Could not provision data:', lvl=error)
            log(format_result(result), lvl=error)
            return False

    if import_file is not None:
        log('Importing backup')
        internal_restore(None, None, {}, 'json', import_file, True, False)

    return True


def _migrate(ctx):
    """Migrate all data objects"""
    # TODO: Implement migration
    log('Would now migrate (Not implemented, yet)')
    return True


@environment.command(name='install', short_help="Install the other environment")
@click.option('--force', '-f', is_flag=True, default=False)
@click.option('--source', '-s', default='git', type=click.Choice(['link', 'copy', 'git']))
@click.option('--url', '-u', default=None)
@click.option('--import-file', '--import', default=None, help='Import the specified backup')
@click.option('--skip-modules', is_flag=True, default=False)
@click.option('--skip-data', is_flag=True, default=False)
@click.option('--skip-frontend', is_flag=True, default=False)
@click.option('--skip-test', is_flag=True, default=False)
@click.pass_context
def install_environment(ctx, source, url, import_file, force, skip_modules, skip_data, skip_frontend, skip_test):
    """Install the non-active environment"""

    if url is None:
        url = source_url

    instance_name = ctx.obj['instance']
    instance_config = ctx.obj['instance_config']

    next_environment = get_next_environment(ctx)

    set_instance(instance_name, next_environment)

    env = instance_config['environments'][next_environment]

    env['database'] = instance_name + '_' + next_environment

    env_path = get_path('lib', '')

    user = instance_config['user']

    log('Installing new other environment for %s on %s from %s in %s' %
        (instance_name, next_environment, source, env_path))

    try:
        result = get_isomer(source, url, env_path, sudo=user)
        if result is False:
            log('Getting Isomer failed', lvl=critical)
            sys.exit(50000)
    except FileExistsError:
        if not force:
            log('Isomer already present, please safely clear or '
                'inspect the environment before continuing! Use --force to ignore.', lvl=warn)
            sys.exit(50000)
        else:
            log('Isomer already present, forcing through anyway.')

    try:
        repository = Repo(os.path.join(env_path, 'repository'))

        log('Repo:', repository, lvl=debug)
        env['version'] = repository.git.describe()
    except (exc.InvalidGitRepositoryError, exc.NoSuchPathError):
        env['version'] = version
        log('Not running from a git repository; Using isomer.version:', version, lvl=warn)

    instance_config['environments'][next_environment] = env
    write_instance(instance_config)

    log('Creating virtual environment')
    success, result = run_process(
        env_path,
        ['virtualenv', '-p', '/usr/bin/python3', '--system-site-packages', 'venv'],
        sudo=user
    )
    if not success:
        log(format_result(result), lvl=error)

    try:
        if _install_backend(ctx):
            log('Backend installed')
            env['installed'] = True
        if not skip_modules and _install_modules(ctx):
            log('Modules installed')
            # env['installed_modules'] = True
        if not skip_data and _install_provisions(ctx, import_file=import_file):
            log('Provisions installed')
            env['provisioned'] = True
        if not skip_data and _migrate(ctx):
            log('Data migrated')
            env['migrated'] = True
        if not skip_frontend and _install_frontend(ctx):
            log('Frontend installed')
            env['frontend'] = True
        if not skip_test and _test_environment(ctx):
            log('Environment tested')
            env['tested'] = True
    except Exception:
        log('Error during installation:', exc=True, lvl=critical)

    log('Environment status now:', env)

    ctx.obj['instance_config']['environments'][next_environment] = env

    write_instance(ctx.obj['instance_config'])


def _install_backend(ctx):
    """Installs the backend into an environment"""

    instance_name = ctx.obj['instance']

    set_instance(instance_name, get_next_environment(ctx))

    env_path = get_path('lib', '')
    user = ctx.obj['instance_config']['user']

    log('Installing backend')
    success, result = run_process(
        os.path.join(env_path, 'repository'),
        [os.path.join(env_path, 'venv', 'bin', 'python3'), 'setup.py', 'develop'],
        sudo=user
    )
    if not success:
        log(format_result(result), lvl=error)

    log('Installing requirements')
    success, result = run_process(
        os.path.join(env_path, 'repository'),
        [os.path.join(env_path, 'venv', 'bin', 'pip3'), 'install', '-r', 'requirements.txt'],
        sudo=user
    )
    if not success:
        log(format_result(result), lvl=error)

    return True
