#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HFOS - Hackerfleet Operating System
# ===================================
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

import grp
import pwd
import sys
import time
import tarfile

from _socket import gethostname
from distutils.dir_util import copy_tree
from subprocess import Popen

import click
import os
import shutil
from OpenSSL import crypto
from click_didyoumean import DYMGroup

from isomer.logger import error, warn, debug
from isomer.misc import std_now
from isomer.tool import check_root, _get_system_configuration, ask, run_process, log, error, debug, verbose
from isomer.tool.etc import NonExistentKey, write_configuration
from isomer.tool.defaults import EXIT_INSTALLATION_FAILED, EXIT_INVALID_ENVIRONMENT, \
    EXIT_PROVISIONING_FAILED, EXIT_USER_BAILED_OUT, EXIT_NOTHING_TO_ARCHIVE, \
    EXIT_INSTANCE_EXISTS, EXIT_INSTANCE_UNKNOWN, EXIT_SERVICE_INVALID, \
    EXIT_INVALID_CONFIGURATION, EXIT_INVALID_SOURCE
from isomer.tool.templates import write_template_file
from isomer.tool.defaults import service_template, cert_file, key_file, distribution, \
    nginx_configuration, combined_file, source_url

from isomer.misc.path import get_path, set_instance, locations

from git import Repo, exc
from isomer.version import version


@click.group(cls=DYMGroup)
@click.pass_context
def instance(ctx):
    """[GROUP] instance various aspects of ISOMER"""

    _get_configuration(ctx)


def _get_configuration(ctx):
    try:
        log('Configuration:', ctx.obj['config'], lvl=verbose, pretty=True)
        log('Instance:', ctx.obj['instance'], lvl=debug)
    except KeyError:
        log('Invalid configuration, stopping.', lvl=error)
        sys.exit(EXIT_INVALID_CONFIGURATION)

    try:
        instance = ctx.obj['config']['instances'][ctx.obj['instance']]
        log('Instance Configuration:', instance, lvl=verbose, pretty=True)

    except NonExistentKey:
        instance = ctx.obj['config']['defaults']

        if ctx.invoked_subcommand not in ('create', 'list'):
            log('Instance %s does not exist' % ctx.obj['instance'], lvl=warn)
            sys.exit(EXIT_INSTANCE_UNKNOWN)

        log('New instance configuration:', instance, lvl=debug)

    environment_name = instance['environment']
    environment = instance['environments'][environment_name]

    try:
        repository = Repo('./')
        ctx.obj['repository'] = repository
        log('Repo:', repository, lvl=debug)
        environment['version'] = repository.git.describe()
    except exc.InvalidGitRepositoryError:
        log('Not running from a git repository; Using isomer.version', lvl=warn)
        environment['version'] = version

    environment['database'] = ctx.obj['instance'] + '_' + environment_name

    ctx.obj['environment'] = environment

    ctx.obj['instance_config'] = instance


@instance.command(short_help="show system configuration of instance")
@click.pass_context
def info(ctx):
    """Print information about the selected instance"""

    log('Instance configuration:', ctx.obj['config'].get('instances', None).get(ctx.obj['instance']), pretty=True)
    log('Environment:', ctx.obj['environment'], pretty=True)
    log('Path:', get_path('cache', 'rastertiles'))


@instance.command(short_help="List all instances")
@click.pass_context
def list(ctx):
    for instance in ctx.obj['config']['instances']:
        log(instance, pretty=True)


@instance.command(short_help="Create a new instance")
@click.pass_context
def create(ctx):
    """Create a new instance"""
    instance_name = ctx.obj['instance']
    if instance_name in ctx.obj['config']['instances']:
        log('Instance exists!', lvl=warn)
        sys.exit(EXIT_INSTANCE_EXISTS)

    log('Creating instance:', instance_name)
    ctx.obj['config']['instances'][instance_name] = ctx.obj['config']['defaults']

    log('config:', ctx.obj['config']['instances'][instance_name], lvl=verbose)
    write_configuration(ctx.obj['config_filename'], ctx.obj['config'])


@instance.command(short_help="Install first environment for instance")
@click.pass_context
def install(ctx):
    """Install a new environment of an instance"""

    log('Would now install a blank instance')


@instance.command(short_help="Clear the whole instance (CAUTION)")
@click.pass_context
def clear_instance(ctx):
    """Clear all environments of an instance"""

    _clear_instance(ctx)


def _clear_instance(ctx):
    log('Clearing instance:', ctx.obj['instance'])
    log('Clearing blue environment.', lvl=debug)
    _clear_environment(ctx, 'blue')
    log('Clearing green environment.', lvl=debug)
    _clear_environment(ctx, 'green')


@instance.command(short_help="Remove a whole instance (CAUTION)")
@click.option('--clear', '-c', is_flag=True, help='Clear instance before removal', default=False)
@click.pass_context
def remove(ctx, clear):
    if clear:
        log('Destructively removing instance:', ctx.obj['instance'], lvl=warn)

    if not ask('Are you sure', default=False, data_type='bool'):
        sys.exit(EXIT_USER_BAILED_OUT)

    if clear:
        _clear_instance(ctx)

    new_config = ctx.obj['config']
    del new_config['instances'][ctx.obj['instance']]

    log(new_config, pretty=True, lvl=debug)
    write_configuration(ctx.obj['config_filename'], new_config)


@click.group(cls=DYMGroup)
@click.pass_context
def environment(ctx):
    """[GROUP] Various aspects of ISOMER environment handling"""

    _get_configuration(ctx)


@environment.command(short_help="Install the other environment")
@click.option('--force', '-f', is_flag=True, default=False)
@click.option('--source', '-s', default='github')
@click.option('--url', '-u', default=None)
@click.pass_context
def install(ctx, source, url, force):
    """Install the non-active environment"""

    if url is None:
        url = source_url

    instance = ctx.obj['instance']
    current_environment = ctx.obj['instance_config']['environment']
    next_environment = 'blue' if current_environment == 'green' else 'green'

    env_path = '/var/lib/isomer/' + instance + '/' + next_environment

    log('Installing new other environment for %s on %s from %s in %s' %
        (instance, next_environment, source, env_path))

    if source != 'github':
        log('Only installing from github is currently supported', lvl=error)
        sys.exit(EXIT_INVALID_SOURCE)

    log('Cloning repository')
    log(run_process(env_path, ['git', 'clone', url, 'repository']), lvl=verbose)

    log('Pulling frontend')
    log(run_process(os.path.join(env_path, 'repository', 'frontend'), ['git', 'pull']), lvl=verbose)

    log('Creating virtual environment')
    log(run_process(env_path, ['virtualenv', '-p', '/usr/bin/python3', '--system-site-packages', 'venv']), lvl=verbose)


def install_backend(ctx):
    """Installs the backend into an environment"""

    instance = ctx.obj['instance']
    current_environment = ctx.obj['instance_config']['environment']
    next_environment = 'blue' if current_environment == 'green' else 'green'

    env_path = '/var/lib/isomer/' + instance + '/' + next_environment

    log('Installing backend')
    log(run_process(os.path.join(env_path, 'repository'),
                    [os.path.join(env_path, 'venv', 'bin', 'python3'), 'setup.py', 'develop']), lvl=verbose)


@environment.command(short_help="Clear the other environment")
@click.option('--force', '-f', is_flag=True, default=False)
@click.pass_context
def clear_environment(ctx, force):
    """Clear the non-active environment"""

    current_environment = ctx.obj['instance_config']['environment']
    next_environment = 'blue' if current_environment == 'green' else 'green'

    log('Clearing other environment:', next_environment)
    set_instance(ctx.obj['instance'], next_environment)

    if _archive(ctx) or force:
        if _clear_environment(ctx, next_environment) or force:
            _create_folders(ctx, next_environment)


def _clear_environment(ctx, environment):
    """Tests an environment for usage, then clears it"""

    log('Testing', environment, 'for usage')

    env = ctx.obj['instance_config']['environments'][environment]

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

    return True

    # TODO:
    # * Remove repository/packages
    # * Remove database


def _create_folders(ctx, environment):
    """Generate required folders for an instance"""

    log("Generating instance directories", emitter='MANAGE')

    env = ctx.obj['instance_config']['environments'][environment]
    instance = ctx.obj['instance_config']

    uid = pwd.getpwnam(instance['user']).pw_uid
    gid = grp.getgrnam(instance['group']).gr_gid

    # If these need changes, make sure they are watertight and don't remove
    # wanted stuff!

    logfile = "/var/log/isomer-" + ctx.obj['instance'] + ".log"

    for item in locations:
        if os.path.exists(item):
            log("Path already exists: " + item)
            return False
        path = get_path(item, '', ensure=True)

        log("Created path: " + path)
        os.chown(path, uid, gid)

    # Touch logfile to make sure it exists
    open(logfile, "a").close()
    os.chown(logfile, uid, gid)

    log("Done: Create instance folders")


@environment.command(short_help="Archive the other environment")
@click.pass_context
def archive(ctx):
    """Archive the non-active  environment"""

    _archive(ctx)


def _archive(ctx):
    current_environment = ctx.obj['instance_config']['environment']
    next_environment = 'blue' if current_environment == 'green' else 'green'

    env = ctx.obj['instance_config']['environments'][next_environment]

    if not env['installed'] or not env['tested']:
        log('Environment has not been installed - not archiving.', lvl=warn)
        return False

    log('Archiving environment:', next_environment)
    set_instance(ctx.obj['instance'], next_environment)

    timestamp = std_now()

    try:
        with tarfile.open(os.path.join('/var/backups/isomer/', timestamp + '.tgz'), 'w:gz') as f:
            for item in locations:
                path = get_path(item, '')
                log('Archiving [%s]: %s' % (item, path))
                f.add(path)
    except (PermissionError, FileNotFoundError) as e:
        log('Could not archive environment:', e, lvl=error)
        return False

    ctx.obj['instance_config']['environments']['archive'][timestamp] = env

    log(ctx.obj['instance_config'])

    return True

    # TODO:
    # * add repository/packages to tarball
    # * export the database to tarball
    # * confirm archival


@instance.command(short_help="Activates the other environment")
@click.pass_context
def activate(ctx):
    """Activates the other environment """

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

    # TODO: Effect reload of service
    # * Systemctl reload
    # * (Re)start service
    # * confirm correct operation
    #  - if not, switch back to the other instance, maybe indicate a broken state for next_environment
    #  - if yes, Store instance configuration and terminate, we're done


def update_service(ctx, next_environment):
    """Updates the specified service configuration"""

    validated, message = validate_services(ctx)

    if not validated:
        log('Service configuration validation failed:', message, lvl=error)
        sys.exit(EXIT_SERVICE_INVALID)

    init = ctx.obj['config']['meta']['init']
    environment = ctx.obj['instance_config']['environments'][next_environment]

    log('Updating %s configuration of instance %s to %s' % (init, ctx.obj['instance'], next_environment))
    log('New environment:', environment, pretty=True)

    # TODO: Add update for systemd
    # * Stop possibly running service (it should not be running, though!)
    # * Actually update service files

    instance = ctx.obj['instance']
    config = ctx.obj['instance_config']

    base_path = os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)),
            '..', '..'))

    env_path = '/var/lib/isomer/' + instance + '/' + next_environment

    log("Updating systemd service for %s (%s)" % (instance, next_environment))

    launcher = os.path.join(env_path, 'src/iso')
    executable = os.path.join(env_path, 'venv/bin/python3') + " " + launcher
    executable += " --instance " + instance

    definitions = {
        'instance': instance,
        'executable': executable,
        'environment': next_environment,
        'user_name': config['user'],
        'user_group': config['group'],
    }
    service_name = 'isomer-' + instance + '.service'

    template_file = os.path.join(base_path, 'dev', 'templates', service_template)

    log('Template:', template_file)
    write_template_file(template_file,
                        os.path.join('/etc/systemd/system/', service_name),
                        definitions)


def _launch_service(ctx):
    """Actually enable and launch newly set up environment"""
    instance = ctx.obj['instance']

    service_name = 'isomer-' + instance + '.service'

    Popen([
        'systemctl',
        'enable',
        service_name
    ])

    log('Launching service')

    Popen([
        'systemctl',
        'start',
        service_name
    ])

    log("Done: Launch Service")


def validate_services(ctx):
    """Checks init configuration settings so nothing gets mis-configured"""

    # TODO:
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

    instance = ctx.obj['instance']
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
        'instance': instance,
        'environment': current_env
    }

    if distribution == 'DEBIAN':
        configuration_file = '/etc/nginx/sites-available/isomer.%s.conf' % instance
        configuration_link = '/etc/nginx/sites-enabled/isomer.%s.conf' % instance
    elif distribution == 'ARCH':
        configuration_file = '/etc/nginx/nginx.conf'
        configuration_link = None
    else:
        log('Unsure how to proceed, you may need to specify your '
            'distribution', lvl=error)
        return

    log('Writing nginx ISOMER site definition')
    write_template_file(os.path.join('dev/templates', nginx_configuration),
                        configuration_file,
                        definitions)

    if configuration_link is not None:
        log('Enabling nginx ISOMER site (symlink)')
        if not os.path.exists(configuration_link):
            os.symlink(configuration_file, configuration_link)

    log('Restarting nginx service')
    Popen([
        'systemctl',
        'restart',
        'nginx.service'
    ])

    log("Done: instance nginx configuration")


@instance.command(short_help='create system user')
def system_user():
    """instance ISOMER system user (isomer.isomer)"""

    add_system_user()
    log("Done: Add User")


def add_system_user():
    """instance ISOMER system user (isomer.isomer)"""

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
    """instance ISOMER system paths (/var/[local,lib,cache]/isomer)"""

    _create_system_folders()
    log("Done: Create system paths")


def _create_system_folders():
    target_paths = [
        '/var/www/challenges',  # For LetsEncrypt acme certificate challenges
        '/var/backups/isomer'
    ]
    for item in locations:
        target_paths.append(get_path(item, ''))

    for item in target_paths:
        try:
            os.mkdir(item)
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

        # TODO

        log('Not implemented yet. You can build your own certificate and '
            'store it in /etc/ssl/certs/isomer/server-cert.pem - it should '
            'be a certificate with key, as this is used server side and '
            'there is no way to enter a separate key.', lvl=error)


@click.command(short_help='Manage updates')
@click.option('--no-restart', help='Do not restart service', is_flag=True, default=False)
@click.option('--no-rebuild', help='Do not rebuild frontend', is_flag=True, default=False)
@click.pass_context
def update(ctx, no_restart, no_rebuild):
    """Update a ISOMER node"""

    # 0. (NOT YET! MAKE A BACKUP OF EVERYTHING)
    # 1. update repository
    # 2. update frontend repository
    # 3. (Not yet: update venv)
    # 4. rebuild frontend
    # 5. restart service

    instance = ctx.obj['instance']

    log('Pulling github updates')
    run_process('.', ['git', 'pull', 'origin', 'master'])
    run_process('./frontend', ['git', 'pull', 'origin', 'master'])

    if not no_rebuild:
        log('Rebuilding frontend')
        # instance_frontend(instance, forcerebuild=True, instance=False, development=True)

    if not no_restart:
        log('Restaring service')
        if instance != 'isomer':
            instance = 'isomer-' + instance

        run_process('.', ['sudo', 'systemctl', 'restart', instance])

    log('Done')
