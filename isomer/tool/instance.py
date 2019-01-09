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
from tempfile import mktemp, mkdtemp

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

import grp
import pwd
import sys
import time
import tarfile

from _socket import gethostname
from distutils.dir_util import copy_tree
from subprocess import Popen

import tomlkit
import click
import os
import shutil
from OpenSSL import crypto
from click_didyoumean import DYMGroup

from isomer.logger import error, warn, debug, critical
from isomer.misc import std_now, std_uuid
from isomer.misc.path import get_path, get_log_path, get_etc_path, set_instance, locations
from isomer.tool import check_root, _get_system_configuration, ask, run_process, get_isomer, format_result, \
    log, error, debug, verbose
from isomer.tool.etc import write_configuration, write_instance, get_etc_instance_path, valid_configuration, \
    remove_instance, NonExistentKey, instance_template, environment_template
from isomer.tool.templates import write_template_file
from isomer.tool.database import delete_database
from isomer.database import backup, initialize
from isomer.tool.defaults import service_template, cert_file, key_file, distribution, \
    nginx_configuration, combined_file, source_url
from isomer.tool.defaults import EXIT_INSTALLATION_FAILED, EXIT_INVALID_ENVIRONMENT, \
    EXIT_PROVISIONING_FAILED, EXIT_USER_BAILED_OUT, EXIT_NOTHING_TO_ARCHIVE, \
    EXIT_INSTANCE_EXISTS, EXIT_INSTANCE_UNKNOWN, EXIT_SERVICE_INVALID, \
    EXIT_INVALID_CONFIGURATION, EXIT_INVALID_SOURCE, EXIT_INVALID_PARAMETER

from git import Repo, exc
from isomer.version import version


@click.group(cls=DYMGroup)
@click.pass_context
def instance(ctx):
    """[GROUP] instance various aspects of Isomer"""

    if ctx.invoked_subcommand in ('info', 'list', 'create'):
        return

    _get_configuration(ctx)


def _get_configuration(ctx):
    try:
        log('Configuration:', ctx.obj['config'], lvl=verbose, pretty=True)
        log('Instance:', ctx.obj['instance'], lvl=debug)
    except KeyError:
        log('Invalid configuration, stopping.', lvl=error)
        sys.exit(EXIT_INVALID_CONFIGURATION)

    try:
        instance_config = ctx.obj['instances'][ctx.obj['instance']]
        log('Instance Configuration:', instance_config, lvl=verbose, pretty=True)
    except NonExistentKey:
        log('Instance %s does not exist' % ctx.obj['instance'], lvl=warn)
        sys.exit(EXIT_INSTANCE_UNKNOWN)

    environment_name = instance_config['environment']
    environment_config = instance_config['environments'][environment_name]

    ctx.obj['environment'] = environment_config

    ctx.obj['instance_config'] = instance_config


@instance.command(name='info', short_help="show system configuration of instance")
@click.pass_context
def info_instance(ctx):
    """Print information about the selected instance"""

    instance_name = ctx.obj['instance']
    instances = ctx.obj['instances']
    instance_config = instances[instance_name]

    environment_name = instance_config['environment']
    environment_config = instance_config['environments'][environment_name]

    if instance_name not in instances:
        log('Instance %s unknown!' % instance_name, lvl=warn)
        sys.exit(EXIT_INSTANCE_UNKNOWN)

    log('Instance configuration:', instance_config, pretty=True)
    log('Active environment (%s):' % environment_name, environment_config, pretty=True)


@instance.command(name='list', short_help='List all instances')
@click.pass_context
def list_instances(ctx):
    """List all known instances"""

    for instance_name in ctx.obj['instances']:
        log(instance_name, pretty=True)


@instance.command(name='set', short_help='Set a parameter of an instance')
@click.argument('parameter')
@click.argument('value')
@click.pass_context
def set_parameter(ctx, parameter, value):
    """Set a configuration parameter of an instance"""

    log('Setting %s to %s' % (parameter, value))
    instance_config = ctx.obj['instance_config']
    defaults = instance_template

    try:
        parameter_type = type(defaults[parameter])
        log(parameter_type, pretty=True, lvl=warn)

        if parameter_type == tomlkit.items.Integer:
            converted_value = int(value)
        elif parameter_type == bool:
            converted_value = value.upper() == 'TRUE'
        else:
            converted_value = value
    except KeyError:
        log('Invalid parameter specified. Available parameters:', sorted(list(defaults.keys())), lvl=warn)
        sys.exit(EXIT_INVALID_PARAMETER)

    instance_config[parameter] = converted_value
    log('New config:', instance_config, pretty=True, lvl=debug)

    ctx.obj['instances'][ctx.obj['instance']] = instance_config

    if valid_configuration(ctx):
        write_instance(instance_config)
    else:
        log('New configuration would not be valid', lvl=critical)
        sys.exit(EXIT_INVALID_CONFIGURATION)


@instance.command(short_help="Create a new instance")
@click.pass_context
def create(ctx):
    """Create a new instance"""
    instance_name = ctx.obj['instance']
    if instance_name in ctx.obj['instances']:
        log('Instance exists!', lvl=warn)
        sys.exit(EXIT_INSTANCE_EXISTS)

    log('Creating instance:', instance_name)
    instance_config = instance_template
    instance_config['name'] = instance_name
    ctx.obj['instances'][instance_name] = instance_config

    write_instance(instance_config)


@instance.command(short_help="Install first environment for instance")
@click.pass_context
def install(ctx):
    """Install a new environment of an instance"""
    # TODO

    log('Would now install a blank instance')


@instance.command(short_help="Clear the whole instance (CAUTION)")
@click.option('--force', '-f', is_flag=True, default=False)
@click.pass_context
def clear_instance(ctx, force):
    """Clear all environments of an instance"""

    _clear_instance(ctx, force)


def _clear_instance(ctx, force):
    log('Clearing instance:', ctx.obj['instance'])
    log('Clearing blue environment.', lvl=debug)
    _clear_environment(ctx, force, 'blue')
    log('Clearing green environment.', lvl=debug)
    _clear_environment(ctx, force, 'green')


@instance.command(short_help="Remove a whole instance (CAUTION)")
@click.option('--clear', '-c', is_flag=True, help='Clear instance before removal', default=False)
@click.pass_context
def remove(ctx, clear):
    """Remove a whole instance"""

    if clear:
        log('Destructively removing instance:', ctx.obj['instance'], lvl=warn)

    if not ask('Are you sure', default=False, data_type='bool'):
        sys.exit(EXIT_USER_BAILED_OUT)

    if clear:
        _clear_instance(ctx, force=True)

    new_config = ctx.obj['config']
    del new_config['instances'][ctx.obj['instance']]

    log(new_config, pretty=True, lvl=debug)
    remove_instance(ctx.obj['instance'])


@click.group(cls=DYMGroup)
@click.pass_context
def environment(ctx):
    """[GROUP] Various aspects of Isomer environment handling"""

    _get_configuration(ctx)


@environment.command(short_help="Install the other environment")
@click.option('--force', '-f', is_flag=True, default=False)
@click.option('--source', '-s', default='git', type=click.Choice(['link', 'copy', 'git']))
@click.option('--url', '-u', default=None)
@click.pass_context
def install(ctx, source, url, force):
    """Install the non-active environment"""

    if url is None:
        url = source_url

    instance_name = ctx.obj['instance']
    instance_config = ctx.obj['instance_config']

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
        log('Picked environment from command line:', next_environment)
    else:
        current_environment = instance_config['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'
        log('Picked environment from configuration:', next_environment)

    set_instance(instance_name, next_environment)

    env = instance_config['environments'][next_environment]
    modules = instance_config['modules']
    log(modules, pretty=True)

    env['database'] = instance_name + '_' + next_environment

    env_path = get_path('lib', '')

    log('Installing new other environment for %s on %s from %s in %s' %
        (instance_name, next_environment, source, env_path))

    result = get_isomer(source, url, env_path)
    if result is False:
        log('Getting Isomer failed', lvl=critical)
        sys.exit(5000)

    try:
        repository = Repo(os.path.join(env_path, 'repository'))

        log('Repo:', repository, lvl=debug)
        env['version'] = repository.git.describe()
    except exc.InvalidGitRepositoryError:
        log('Not running from a git repository; Using isomer.version', lvl=warn)
        env['version'] = version

    instance_config['environments'][next_environment] = env
    write_instance(instance_config)

    log('Creating virtual environment')
    success, result = run_process(env_path, ['virtualenv', '-p', '/usr/bin/python3', '--system-site-packages', 'venv'])
    if not success:
        log(format_result(result), lvl=error)

    if _install_backend(ctx) and _install_modules(next_environment, modules):
        log('Backend and modules successfully installed')
        env['installed'] = True
    if _install_provisions(instance_config, next_environment):
        log('Provisions installed')
        env['provisioned'] = True
    if _migrate(instance_config, next_environment):
        log('Data migrated')
        env['migrated'] = True
    if _install_frontend(instance_config, next_environment):
        log('Frontend installed')
        env['frontend'] = True
    if _test_environment(instance_config, next_environment):
        log('Environment tested')
        env['tested'] = True

    log('Environment now:', env)

    ctx.obj['instance_config']['environments'][next_environment] = env

    write_instance(ctx.obj['instance_config'])


def _install_backend(ctx):
    """Installs the backend into an environment"""

    instance_name = ctx.obj['instance']

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
    else:
        current_environment = ctx.obj['instance_config']['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'

    set_instance(instance_name, next_environment)

    env_path = get_path('lib', '')

    log('Installing backend')
    success, result = run_process(os.path.join(env_path, 'repository'),
                                  [os.path.join(env_path, 'venv', 'bin', 'python3'), 'setup.py', 'develop'])
    if not success:
        log(format_result(result), lvl=error)

    log('Installing requirements')
    success, result = run_process(os.path.join(env_path, 'repository'),
                                  [os.path.join(env_path, 'venv', 'bin', 'pip3'), 'install', '-r', 'requirements.txt'])
    if not success:
        log(format_result(result), lvl=error)

    return True


@instance.command('install-module', short_help="Add (and install) a module to an instance")
@click.option('--source', '-s', default='github')
@click.option('--url', '-u', default=None)
@click.option('--install-env', '--install', '-i', is_flag=True, default=False,
              help='Install module on active environment')
@click.pass_context
def install_instance_module(ctx, source, url, install_env):
    """Add and install a module"""

    instance_name = ctx.obj['instance']
    instance_configuration = ctx.obj['instances'][instance_name]

    descriptor = {'source': source, 'url': url}
    instance_configuration['modules'].append(descriptor)

    write_instance(instance_configuration)

    if install_env is True:
        install_environment_module(ctx, source, url)

    log('Done: Install instance module')


@environment.command('install-module', short_help="Install a module into an environment")
@click.option('--source', '-s', default='github')
@click.option('--url', '-u', default=None)
@click.pass_context
def install_environment_module(ctx, source, url):
    """Add and install a module"""

    instance_name = ctx.obj['instance']
    instance_configuration = ctx.obj['instances'][instance_name]

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
    else:
        current_environment = ctx.obj['instance_config']['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'

    set_instance(instance_name, next_environment)

    if _install_module(source, url):
        descriptor = {'source': source, 'url': url}
        instance_configuration['environments']['modules'].append(descriptor)

    write_instance(instance_configuration)

    log('Done: Install environment module')


def _install_module(source, url):
    """Actually installs a module into an environment"""

    module_path = get_path('lib', 'modules', ensure=True)

    if source not in ('git', 'link', 'copy'):
        log('Only installing from github or local is currently supported', lvl=error)
        sys.exit(EXIT_INVALID_SOURCE)

    uuid = std_uuid()
    temporary_path = os.path.join(module_path, '%s' % uuid)

    if source == 'git':
        log('Cloning repository from', url)
        success, output = run_process(module_path, ['git', 'clone', url, temporary_path])
        if not success:
            log('Error:', output, lvl=error)
    elif source == 'link':
        log('Linking repository from', url)
        success, output = run_process(module_path, ['ln', '-s', url, temporary_path])
        if not success:
            log('Error:', output, lvl=error)

    log('Getting name')
    success, result = run_process(temporary_path, ['python', 'setup.py', '--name'])
    if not success:
        log(format_result(result), pretty=True, lvl=error)
        return False

    package_name = str(result.output, encoding='utf8').rstrip('\n')
    log('Package name:', package_name, type(package_name))

    final_path = os.path.join(module_path, package_name)

    log('Renaming to', final_path)
    os.rename(temporary_path, final_path)

    log('Installing module')
    success, output = run_process(final_path,
                                  [os.path.join(get_path('lib', 'venv'), 'bin', 'python3'), 'setup.py', 'develop'])
    if not success:
        log(output, lvl=verbose)
        return False
    else:
        return True


def _install_modules(env, modules):
    """Install all given modules"""

    log('Installing modules into', env, pretty=True)

    for module in modules:
        log(module, pretty=True)
        _install_module(module['source'], module['url'])

    # TODO: Confirm in environment configuration which modules are installed

    return True


@environment.command(short_help='Install provisions and/or a database dump')
@click.pass_context
def install_provisions(ctx):
    """Foo"""
    _install_provisions(ctx.obj['instance_config'], ctx.obj['environment'])


def _install_provisions(instance_config, env):
    """Load provisions into database"""

    env_path = get_path('lib', '')

    # TODO: Dependencies of provisions!
    # First, user has to be provisioned, then system, then the rest

    success, result = run_process(os.path.join(env_path, 'repository'), [
        os.path.join(env_path, 'venv', 'bin', 'python3'),
        './iso', '-nc', '--clog', '5', '--config-dir', get_etc_path(), '-i', instance_config['name'], '-e', env,
        'install', 'provisions'])
    if not success:
        log(format_result(result), lvl=error)
        return False

    return True


def _migrate(instance_config, env):
    """Migrate all data objects"""
    # TODO: log('Would now migrate')
    return True


@environment.command(short_help='Install frontend')
@click.pass_context
def install_frontend(ctx):
    """Foo"""

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
    else:
        current_environment = ctx.obj['instance_config']['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'

    set_instance(ctx.obj['instance'], next_environment)
    _install_frontend(ctx.obj['instance_config'], next_environment)


def _install_frontend(instance_config, env):
    """Install and build the frontend"""

    env_path = get_path('lib', '')

    success, result = run_process(os.path.join(env_path, 'repository'), [
        os.path.join(env_path, 'venv', 'bin', 'python3'),
        './iso', '-nc', '--config-dir', get_etc_path(), '-i', instance_config['name'], '-e', env,
        'install', 'frontend', '--rebuild'])
    if not success:
        log(format_result(result), lvl=error)
        return False

    return True


def _test_environment(instance_config, env):
    """General fitness tests of the built environment"""
    # TODO: log('Would now test the environment')
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
        current_environment = ctx.obj['instance_config']['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'
    else:
        next_environment = clear_env

    log('Clearing other environment:', next_environment)
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

    logfile = os.path.join(get_log_path(), "isomer-" + ctx.obj['instance'] + ".log")

    for item in locations:
        path = get_path(item, '', ensure=True)

        if os.path.exists(path):
            log("Path already exists:", path)

        log("Created path: " + path)
        if os.geteuid() == 0 and uid is not None:
            os.chown(path, uid, gid)
        else:
            log('No root access - could not change ownership', lvl=warn)

    module_path = get_path('lib', 'modules', ensure=True)
    log('Module storage created:', module_path)

    # Touch logfile to make sure it exists
    open(logfile, "a").close()
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

    if ctx.obj['acting_environment'] is not None:
        next_environment = ctx.obj['acting_environment']
    else:
        current_environment = instance_config['environment']
        next_environment = 'blue' if current_environment == 'green' else 'green'

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


@instance.command(short_help="Activates the other environment")
@click.pass_context
def turnover(ctx):
    """Activates the other environment """

    # if ctx.obj['acting_environment'] is not None:
    #    next_environment = ctx.obj['acting_environment']
    # else:
    current_environment = ctx.obj['instance_config']['environment']
    next_environment = 'blue' if current_environment == 'green' else 'green'

    log('Activating environment:', next_environment)
    env = ctx.obj['instance_config']['environments'][next_environment]

    log('Inspecting new environment')

    if not env.get('installed', False) or not env.get('tested', False) or \
            not env.get('provisioned', False) or not env.get('migrated', False):
        log('Installation failed, cannot activate!')
        sys.exit(EXIT_INSTALLATION_FAILED)

    update_service(ctx, next_environment)

    ctx.obj['instance_config']['environment'] = next_environment

    write_instance(ctx.obj['instance_config'])

    # TODO: Effect reload of service
    # * Systemctl reload
    # * (Re)start service
    # * confirm correct operation
    #  - if not, switch back to the other instance, maybe indicate a broken state for next_environment
    #  - if yes, Store instance configuration and terminate, we're done

    log('Done: Turnover to', next_environment)


def update_service(ctx, next_environment):
    """Updates the specified service configuration"""

    validated, message = validate_services(ctx)

    if not validated:
        log('Service configuration validation failed:', message, lvl=error)
        sys.exit(EXIT_SERVICE_INVALID)

    init = ctx.obj['config']['meta']['init']
    environment_config = ctx.obj['instance_config']['environments'][next_environment]

    log('Updating %s configuration of instance %s to %s' % (init, ctx.obj['instance'], next_environment))
    log('New environment:', environment_config, pretty=True)

    # TODO: Add update for systemd
    # * Stop possibly running service (it should not be running, though!)
    # * Actually update service files

    instance_name = ctx.obj['instance']
    config = ctx.obj['instance_config']

    base_path = os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)),
            '..', '..'))

    env_path = '/var/lib/isomer/' + instance_name + '/' + next_environment

    log("Updating systemd service for %s (%s)" % (instance_name, next_environment))

    launcher = os.path.join(env_path, 'repository/iso')
    executable = os.path.join(env_path, 'venv/bin/python3') + " " + launcher
    executable += " --instance " + instance_name + ' launch'

    definitions = {
        'instance': instance_name,
        'executable': executable,
        'environment': next_environment,
        'user_name': config['user'],
        'user_group': config['group'],
    }
    service_name = 'isomer-' + instance_name + '.service'

    template_file = os.path.join(base_path, 'dev', 'templates', service_template)

    log('Template:', template_file)
    write_template_file(template_file,
                        os.path.join('/etc/systemd/system/', service_name),
                        definitions)


def _launch_service(ctx):
    """Actually enable and launch newly set up environment"""
    instance_name = ctx.obj['instance']

    service_name = 'isomer-' + instance_name + '.service'

    success, result = run_process('/', ['systemctl', 'enable', service_name])

    if not success:
        log('Error activating service:', format_result(result), pretty=True, lvl=error)
        sys.exit(5000)

    log('Launching service')

    success, result = run_process('/', ['systemctl', 'start', service_name])

    if not success:
        log('Error activating service:', format_result(result), pretty=True, lvl=error)
        sys.exit(5000)

    log("Done: Launch Service")


def validate_services(ctx):
    """Checks init configuration settings so nothing gets mis-configured"""

    # TODO: Service validation
    # * Check through all configurations that we're not messing with port numbers
    # * ???

    return True, "VALIDATION_NOT_IMPLEMENTED"


@instance.command(short_help='install systemd service')
@click.pass_context
def service(ctx):
    """instance systemd service configuration"""

    update_service(ctx, ctx.obj['instance_config']['environment'])
    log('Done: Update init service')


@instance.command(short_help='instance nginx configuration')
@click.option('--hostname', default=None,
              help='Override public Hostname (FQDN) Default from active system '
                   'configuration')
@click.pass_context
def update_nginx(ctx, hostname):
    """instance nginx configuration"""

    ctx.obj['hostname'] = hostname

    _create_nginx_config(ctx)
    log("Done: Update nginx config")


def _create_nginx_config(ctx):
    """instance nginx configuration"""

    # TODO: Specify template url very precisely. Currently one needs to be in the repository root

    instance_name = ctx.obj['instance']
    config = ctx.obj['instance_config']

    current_env = config['environment']
    env = config['environments'][current_env]

    dbhost = config['database_host']
    dbname = env['database']

    hostname = ctx.obj['hostname']
    if hostname is None:
        hostname = config['web_hostname']
    if hostname is None:
        try:
            configuration = _get_system_configuration(dbhost, dbname)
            hostname = configuration.hostname
        except Exception as e:
            log('Exception:', e, type(e), exc=True, lvl=error)
            log("""Could not determine public fully qualified hostname!
Check systemconfig (see db view and db modify commands) or specify
manually with --hostname host.domain.tld

Using 'localhost' for now""", lvl=warn)
            hostname = 'localhost'
    port = config['web_port']

    log("Creating nginx configuration for %s:%i using %s@%s" % (hostname, port, dbname, dbhost))

    definitions = {
        'server_public_name': hostname,
        'ssl_certificate': cert_file,
        'ssl_key': key_file,
        'host_url': 'http://127.0.0.1:%i/' % port,
        'instance': instance_name,
        'environment': current_env
    }

    if distribution == 'DEBIAN':
        configuration_file = '/etc/nginx/sites-available/isomer.%s.conf' % instance_name
        configuration_link = '/etc/nginx/sites-enabled/isomer.%s.conf' % instance_name
    elif distribution == 'ARCH':
        configuration_file = '/etc/nginx/nginx.conf'
        configuration_link = None
    else:
        log('Unsure how to proceed, you may need to specify your '
            'distribution', lvl=error)
        return

    log('Writing nginx Isomer site definition')
    write_template_file(os.path.join('dev/templates', nginx_configuration),
                        configuration_file,
                        definitions)

    if configuration_link is not None:
        log('Enabling nginx Isomer site (symlink)')
        if not os.path.exists(configuration_link):
            os.symlink(configuration_file, configuration_link)

    log('Restarting nginx service')
    Popen([
        'systemctl',
        'restart',
        'nginx.service'
    ])

    log("Done: instance nginx configuration")


# TODO: Add instance user

@instance.command(short_help='create system user')
def system_user():
    """instance Isomer system user (isomer.isomer)"""

    add_system_user()
    log("Done: Add User")


def add_system_user():
    """instance Isomer system user (isomer.isomer)"""

    check_root()

    Popen([
        '/usr/sbin/adduser',
        '--system',
        '--quiet',
        '--home',
        '/var/run/isomer',
        '--group',
        '--disabled-password',
        '--disabled-login',
        'isomer'
    ])
    time.sleep(2)


@instance.command(short_help='create system paths')
def system_paths():
    """instance Isomer system paths (/var/[local,lib,cache]/isomer)"""

    _create_system_folders()
    log("Done: Create system paths")


def _create_system_folders():
    target_paths = [
        '/var/www/challenges',  # For LetsEncrypt acme certificate challenges
        '/var/backups/isomer',
    ]
    for item in locations:
        target_paths.append(get_path(item, ''))

    target_paths.append(get_log_path())

    for item in target_paths:
        try:
            os.makedirs(item, exist_ok=True)
        except FileExistsError:
            log('Location already present:', item)
            pass


@instance.command(short_help='instance ssl certificate')
@click.option('--selfsigned', help="Use a self-signed certificate",
              default=True, is_flag=True)
def cert(selfsigned):
    """instance a local SSL certificate"""

    instance_cert(selfsigned)


def instance_cert(selfsigned):
    """instance a local SSL certificate"""

    check_root()

    if selfsigned:
        log('Generating self signed (insecure) certificate/key '
            'combination')

        try:
            os.mkdir('/etc/ssl/certs/isomer')
        except FileExistsError:
            pass
        except PermissionError:
            log("Need root (e.g. via sudo) to generate ssl certificate")
            sys.exit(1)

        def create_self_signed_cert():
            """Create a simple self signed SSL certificate"""

            # create a key pair
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 1024)

            if os.path.exists(cert_file):
                try:
                    certificate = open(cert_file, "rb").read()
                    old_cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                                       certificate)
                    serial = old_cert.get_serial_number() + 1
                except (crypto.Error, OSError) as e:
                    log('Could not read old certificate to increment '
                        'serial:', type(e), e, exc=True, lvl=warn)
                    serial = 1
            else:
                serial = 1

            # create a self-signed certificate
            certificate = crypto.X509()
            certificate.get_subject().C = "DE"
            certificate.get_subject().ST = "Berlin"
            certificate.get_subject().L = "Berlin"
            # noinspection PyPep8
            certificate.get_subject().O = "Hackerfleet"
            certificate.get_subject().OU = "Hackerfleet"
            certificate.get_subject().CN = gethostname()
            certificate.set_serial_number(serial)
            certificate.gmtime_adj_notBefore(0)
            certificate.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
            certificate.set_issuer(certificate.get_subject())
            certificate.set_pubkey(k)
            certificate.sign(k, b'sha512')

            open(key_file, "wt").write(str(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, k),
                encoding="ASCII"))

            open(cert_file, "wt").write(str(
                crypto.dump_certificate(crypto.FILETYPE_PEM, certificate),
                encoding="ASCII"))

            open(combined_file, "wt").write(str(
                crypto.dump_certificate(crypto.FILETYPE_PEM, certificate),
                encoding="ASCII") + str(
                crypto.dump_privatekey(crypto.FILETYPE_PEM, k),
                encoding="ASCII"))

        create_self_signed_cert()

        log('Done: instance Cert')
    else:
        # TODO: Add certbot certificate handling for instances

        log('Not implemented yet. You can build your own certificate and '
            'store it in /etc/ssl/certs/isomer/server-cert.pem - it should '
            'be a certificate with key, as this is used server side and '
            'there is no way to enter a separate key.', lvl=error)
