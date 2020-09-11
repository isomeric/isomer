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

Module: Instance
================

Instance management functionality.

    instance info
    instance list
    instance set
    instance create
    instance install
    instance clear
    instance remove
    instance install-module
    instance turnover
    instance cert
    instance service
    instance update-nginx

"""

import os
import webbrowser
from socket import gethostname
from shutil import rmtree

import tomlkit
import click
from click_didyoumean import DYMGroup
from isomer.error import (
    abort,
    EXIT_INVALID_CONFIGURATION,
    EXIT_INSTALLATION_FAILED,
    EXIT_INSTANCE_EXISTS,
    EXIT_INSTANCE_UNKNOWN,
    EXIT_SERVICE_INVALID,
    EXIT_USER_BAILED_OUT,
    EXIT_INVALID_PARAMETER,
)
from isomer.migration import apply_migrations
from isomer.misc import sorted_alphanumerical
from isomer.misc.path import set_instance, get_etc_instance_path, get_path
from isomer.logger import warn, critical
from isomer.tool import (
    _get_system_configuration,
    _get_configuration,
    get_next_environment,
    ask,
    finish,
    run_process,
    format_result,
    log,
    error,
    debug,
)
from isomer.tool.etc import (
    write_instance,
    valid_configuration,
    remove_instance,
    instance_template,
)
from isomer.tool.templates import write_template
from isomer.tool.defaults import (
    service_template,
    nginx_template,
    distribution,
)
from isomer.tool.environment import (
    _install_environment,
    install_environment_modules,
    _clear_environment,
    _check_environment,
)
from isomer.tool.database import copy_database
from isomer.tool.version import _get_versions
from isomer.ui.builder import copy_directory_tree
from isomer.ui.store import DEFAULT_STORE_URL


@click.group(cls=DYMGroup)
@click.pass_context
def instance(ctx):
    """[GROUP] instance various aspects of Isomer"""

    if ctx.invoked_subcommand in ("info", "list", "create"):
        return

    _get_configuration(ctx)


@instance.command(name="info", short_help="show system configuration of instance")
@click.pass_context
def info_instance(ctx):
    """Print information about the selected instance"""

    instance_name = ctx.obj["instance"]
    instances = ctx.obj["instances"]
    instance_configuration = instances[instance_name]

    environment_name = instance_configuration["environment"]
    environment_config = instance_configuration["environments"][environment_name]

    if instance_name not in instances:
        log("Instance %s unknown!" % instance_name, lvl=warn)
        abort(EXIT_INSTANCE_UNKNOWN)

    log("Instance configuration:", instance_configuration, pretty=True)
    log("Active environment (%s):" % environment_name, environment_config, pretty=True)

    finish(ctx)


@instance.command(
    name="check", short_help="check instance configuration and environments"
)
@click.pass_context
def check_instance(ctx):
    """Check health of the selected instance"""

    instance_name = ctx.obj["instance"]
    instances = ctx.obj["instances"]
    instance_configuration = instances[instance_name]

    environment_name = instance_configuration["environment"]
    environment_config = instance_configuration["environments"][environment_name]

    if instance_name not in instances:
        log("Instance %s unknown!" % instance_name, lvl=warn)
        abort(EXIT_INSTANCE_UNKNOWN)

    # TODO: Validate instance config

    _check_environment(ctx, "blue")
    _check_environment(ctx, "green")

    finish(ctx)


@instance.command(name="browser", short_help="try to point a browser to this instance")
@click.pass_context
def browser(ctx):
    """Tries to start or point a browser towards this instance's frontend"""
    instance_configuration = ctx.obj["instance_configuration"]

    server = instance_configuration.get("webserver", "internal")
    protocol = "http"

    if server != "internal":
        protocol += "s"

    host = instance_configuration.get(
        "web_hostname", instance_configuration.get("web_address", "127.0.0.1")
    )
    port = instance_configuration.get("web_port", None)

    if port is None:
        url = "%s://%s" % (protocol, host)
    else:
        url = "%s://%s:%i" % (protocol, host, port)

    log("Opening browser to:", url)
    log(
        "If this is empty or unreachable, check your instance with:\n"
        "   iso instance info\n"
        "Also try the health checks:\n"
        "   iso instance check"
    )

    webbrowser.open(url)


@instance.command(name="list", short_help="List all instances")
@click.pass_context
def list_instances(ctx):
    """List all known instances"""

    for instance_name in ctx.obj["instances"]:
        log(instance_name, pretty=True)
    finish(ctx)


@instance.command(name="set", short_help="Set a parameter of an instance")
@click.argument("parameter")
@click.argument("value")
@click.pass_context
def set_parameter(ctx, parameter, value):
    """Set a configuration parameter of an instance"""

    log("Setting %s to %s" % (parameter, value))
    instance_configuration = ctx.obj["instance_configuration"]
    defaults = instance_template
    converted_value = None

    try:
        parameter_type = type(defaults[parameter])
        log(parameter_type, pretty=True, lvl=debug)

        if parameter_type == tomlkit.items.Integer:
            converted_value = int(value)
        elif parameter_type == bool:
            converted_value = value.upper() == "TRUE"
        else:
            converted_value = value
    except KeyError:
        log("Available parameters:", sorted(list(defaults.keys())))
        abort(EXIT_INVALID_PARAMETER)

    if converted_value is None:
        log("Converted value was None! Recheck the new config!", lvl=warn)

    instance_configuration[parameter] = converted_value
    log("New config:", instance_configuration, pretty=True, lvl=debug)

    ctx.obj["instances"][ctx.obj["instance"]] = instance_configuration

    if valid_configuration(ctx):
        write_instance(instance_configuration)
        finish(ctx)
    else:
        log("New configuration would not be valid", lvl=critical)
        abort(EXIT_INVALID_CONFIGURATION)


@instance.command(short_help="Create a new instance")
@click.argument("instance_name", default="")
@click.pass_context
def create(ctx, instance_name):
    """Create a new instance"""

    if instance_name is "":
        instance_name = ctx.obj["instance"]

    if instance_name in ctx.obj["instances"]:
        abort(EXIT_INSTANCE_EXISTS)

    log("Creating instance:", instance_name)
    instance_configuration = instance_template
    instance_configuration["name"] = instance_name
    ctx.obj["instances"][instance_name] = instance_configuration

    write_instance(instance_configuration)
    finish(ctx)


@instance.command(name="install", short_help="Install a fresh instance")
@click.option("--force", "-f", is_flag=True, default=False)
@click.option(
    "--source", "-s", default="git",
    type=click.Choice(["link", "copy", "git", "github"])
)
@click.option("--url", "-u", default="", type=click.Path())
@click.option(
    "--import-file", "--import", default=None, help="Import the specified backup"
)
@click.option(
    "--no-sudo",
    is_flag=True,
    default=False,
    help="Do not use sudo to install (Mostly for tests)",
)
@click.option(
    "--release", "-r", default=None, help="Override installed release version"
)
@click.option("--skip-modules", is_flag=True, default=False)
@click.option("--skip-data", is_flag=True, default=False)
@click.option("--skip-frontend", is_flag=True, default=False)
@click.option("--skip-test", is_flag=True, default=False)
@click.option("--skip-provisions", is_flag=True, default=False)
@click.pass_context
def install(ctx, **kwargs):
    """Install a new environment of an instance"""

    log("Installing instance")

    env = ctx.obj["instance_configuration"]["environments"]

    green = env["green"]["installed"]
    blue = env["blue"]["installed"]

    if green or blue:
        log(
            "At least one environment is installed or in a non-clear state.\n"
            "Please use 'iso instance upgrade' to upgrade an instance.",
            lvl=warn,
        )
        abort(50081)

    _clear_instance(ctx, force=kwargs["force"], clear=False, no_archive=True)

    _install_environment(ctx, **kwargs)

    ctx.obj["instance_configuration"]["source"] = kwargs["source"]
    ctx.obj["instance_configuration"]["url"] = kwargs["url"]

    write_instance(ctx.obj["instance_configuration"])

    _turnover(ctx, force=kwargs["force"])

    finish(ctx)


@instance.command(name="clear", short_help="Clear the whole instance (CAUTION)")
@click.option("--force", "-f", is_flag=True, default=False)
@click.option("--no-archive", "-n", is_flag=True, default=False)
@click.pass_context
def clear_instance(ctx, force, no_archive):
    """Irrevocably clear all environments of an instance"""

    _clear_instance(ctx, force, False, no_archive)


def _clear_instance(ctx, force, clear, no_archive):
    log("Clearing instance:", ctx.obj["instance"])
    log("Clearing blue environment.", lvl=debug)
    _clear_environment(ctx, force, "blue", clear, no_archive)
    log("Clearing green environment.", lvl=debug)
    _clear_environment(ctx, force, "green", clear, no_archive)
    finish(ctx)


@instance.command(short_help="Remove a whole instance (CAUTION)")
@click.option(
    "--clear", "-c", is_flag=True, help="Clear instance before removal", default=False
)
@click.option("--no-archive", "-n", is_flag=True, default=False)
@click.pass_context
def remove(ctx, clear, no_archive):
    """Irrevocably remove a whole instance"""

    if clear:
        log("Destructively removing instance:", ctx.obj["instance"], lvl=warn)

    if not ask("Are you sure", default=False, data_type="bool"):
        abort(EXIT_USER_BAILED_OUT)

    if clear:
        _clear_instance(ctx, force=True, clear=clear, no_archive=no_archive)

    remove_instance(ctx.obj["instance"])
    finish(ctx)


@instance.command(
    "install-modules", short_help="Add (and install) modules to an instance"
)
@click.option(
    "--source",
    "-s",
    default="git",
    type=click.Choice(["link", "copy", "git", "develop", "store"]),
    help="Specify installation source/method",
)
@click.option(
    "--store-url",
    default=DEFAULT_STORE_URL,
    help="Specify alternative store url (Default: %s)" % DEFAULT_STORE_URL,
)
@click.option(
    "--install-env",
    "--install",
    "-i",
    is_flag=True,
    default=False,
    help="Install modules on active environment",
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Force installation (overwrites old modules)",
)
@click.argument("urls", nargs=-1)
@click.pass_context
def install_instance_modules(ctx, source, urls, install_env, force, store_url):
    """Add (and optionally immediately install) modules for an instance.

    This will add them to the instance's configuration, so they will be upgraded as well
    as reinstalled on other environment changes.

    If you're installing from a store, you can specify a custom store URL with the
    --store-url argument.
    """

    instance_name = ctx.obj["instance"]
    instance_configuration = ctx.obj["instances"][instance_name]

    for url in urls:
        descriptor = [source, url]
        if store_url != DEFAULT_STORE_URL:
            descriptor.append(store_url)
        if descriptor not in instance_configuration["modules"]:
            instance_configuration["modules"].append(descriptor)
        elif not force:
            log("Module %s is already installed. Use --force to install anyway." % url)
            abort(50000)

    write_instance(instance_configuration)

    if install_env is True:
        next_environment = get_next_environment(ctx)
        environments = instance_configuration['environments']

        if environments[next_environment]["installed"] is False:
            log("Environment %s is not installed, cannot install modules."
                % next_environment, lvl=warn)
            abort(50600)
            return
        del ctx.params["install_env"]
        ctx.forward(install_environment_modules)

    finish(ctx)


@instance.command(short_help="Activates the other environment")
@click.option("--force", "-f", is_flag=True, default=False, help="Force turnover")
@click.pass_context
def turnover(ctx, **kwargs):
    """Activates the other environment """

    _turnover(ctx, **kwargs)
    finish(ctx)


def _turnover(ctx, force):
    """Internal turnover operation"""

    # if ctx.obj['acting_environment'] is not None:
    #    next_environment = ctx.obj['acting_environment']
    # else:
    next_environment = get_next_environment(ctx)

    log("Activating environment:", next_environment)
    env = ctx.obj["instance_configuration"]["environments"][next_environment]

    log("Inspecting new environment")

    if not force:
        if env.get("database", "") == "":
            log("Database has not been set up correctly.", lvl=critical)
            abort(EXIT_INSTALLATION_FAILED)

        if (
                not env.get("installed", False)
                or not env.get("tested", False)
                or not env.get("migrated", False)
        ):
            log("Installation failed, cannot activate!", lvl=critical)
            abort(EXIT_INSTALLATION_FAILED)

    update_service(ctx, next_environment)

    ctx.obj["instance_configuration"]["environment"] = next_environment

    write_instance(ctx.obj["instance_configuration"])

    # TODO: Effect reload of service
    #  * Systemctl reload
    #  * (Re)start service
    #  * confirm correct operation
    #   - if not, switch back to the other instance, maybe indicate a broken
    #     state for next_environment
    #   - if yes, Store instance configuration and terminate, we're done

    log("Turned instance over to", next_environment)


@instance.command(short_help="Upgrades the other environment")
@click.option("--release", "-r", default=None, help="Specify release to upgrade to")
@click.option("--upgrade-modules", default=False, is_flag=True,
              help="Also, upgrade modules if possible")
@click.option("--restart", default=False, is_flag=True,
              help="Restart systemd service via systemctl on success")
@click.option("--handle-cache", "-c",
              type=click.Choice(["ignore", "move", "copy"], case_sensitive=False),
              default="ignore", help="Handle cached data as well (ignore, move, copy)")
@click.option(
    "--source",
    "-s",
    default="git",
    type=click.Choice(["link", "copy", "git", "develop", "github", "pypi"]),
    help="Specify installation source/method",
)
@click.option("--url", "-u", default="", type=click.Path())
@click.pass_context
def upgrade(ctx, release, upgrade_modules, restart, handle_cache, source, url):
    """Upgrades an instance on its other environment and turns over on success.

    \b
    1. Test if other environment is empty
    1.1. No - archive and clear it
    2. Copy current environment to other environment
    3. Clear old bits (venv, frontend)
    4. Fetch updates in other environment repository
    5. Select a release
    6. Checkout that release and its submodules
    7. Install release
    8. Copy database
    9. Migrate data (WiP)
    10. Turnover

    """

    instance_config = ctx.obj["instance_configuration"]
    repository = get_path("lib", "repository")

    installation_source = source if source is not None else instance_config['source']
    installation_url = url if url is not None else instance_config['url']

    environments = instance_config["environments"]

    active = instance_config["environment"]

    next_environment = get_next_environment(ctx)
    if environments[next_environment]["installed"] is True:
        _clear_environment(ctx, clear_env=next_environment)

    source_paths = [
        get_path("lib", "", environment=active),
        get_path("local", "", environment=active)
    ]

    destination_paths = [
        get_path("lib", "", environment=next_environment),
        get_path("local", "", environment=next_environment)
    ]

    log(source_paths, destination_paths, pretty=True)

    for source, destination in zip(source_paths, destination_paths):
        log("Copying to new environment:", source, destination)
        copy_directory_tree(source, destination)

    if handle_cache != "ignore":
        log("Handling cache")
        move = handle_cache == "move"
        copy_directory_tree(
            get_path("cache", "", environment=active),
            get_path("cache", "", environment=next_environment),
            move=move
        )

    rmtree(get_path("lib", "venv"), ignore_errors=True)
    # TODO: This potentially leaves frontend-dev:
    rmtree(get_path("lib", "frontend"), ignore_errors=True)

    releases = _get_versions(
        ctx,
        source=installation_source,
        url=installation_url,
        fetch=True
    )

    releases_keys = sorted_alphanumerical(releases.keys())

    if release is None:
        release = releases_keys[-1]
    else:
        if release not in releases_keys:
            log("Unknown release. Maybe try a different release or source.")
            abort(50100)

    log("Choosing release", release)

    _install_environment(
        ctx, installation_source, installation_url, upgrade=True, release=release
    )

    new_database_name = instance_config["name"] + "_" + next_environment

    copy_database(
        ctx.obj["dbhost"],
        active['database'],
        new_database_name
    )

    apply_migrations(ctx)

    finish(ctx)


def update_service(ctx, next_environment):
    """Updates the specified service configuration"""

    validated, message = validate_services(ctx)

    if not validated:
        log("Service configuration validation failed:", message, lvl=error)
        abort(EXIT_SERVICE_INVALID)

    init = ctx.obj["config"]["meta"]["init"]
    environment_config = ctx.obj["instance_configuration"]["environments"][
        next_environment
    ]

    log(
        "Updating %s configuration of instance %s to %s"
        % (init, ctx.obj["instance"], next_environment)
    )
    log("New environment:", environment_config, pretty=True)

    # TODO: Add update for systemd
    # * Stop possibly running service (it should not be running, though!)
    # * Actually update service files

    instance_name = ctx.obj["instance"]
    config = ctx.obj["instance_configuration"]

    env_path = "/var/lib/isomer/" + instance_name + "/" + next_environment

    log("Updating systemd service for %s (%s)" % (instance_name, next_environment))

    launcher = os.path.join(env_path, "repository/iso")
    executable = os.path.join(env_path, "venv/bin/python3") + " " + launcher
    executable += " --quiet --instance " + instance_name + " launch"

    definitions = {
        "instance": instance_name,
        "executable": executable,
        "environment": next_environment,
        "user_name": config["user"],
        "user_group": config["group"],
    }
    service_name = "isomer-" + instance_name + ".service"

    write_template(
        service_template,
        os.path.join("/etc/systemd/system/", service_name),
        definitions,
    )


def _launch_service(ctx):
    """Actually enable and launch newly set up environment"""
    instance_name = ctx.obj["instance"]

    service_name = "isomer-" + instance_name + ".service"

    success, result = run_process(
        "/", ["systemctl", "enable", service_name], sudo="root"
    )

    if not success:
        log("Error activating service:", format_result(result), pretty=True, lvl=error)
        abort(5000)

    log("Launching service")

    success, result = run_process(
        "/", ["systemctl", "start", service_name], sudo="root"
    )

    if not success:
        log("Error activating service:", format_result(result), pretty=True, lvl=error)
        abort(5000)

    return True


def validate_services(ctx):
    """Checks init configuration settings so nothing gets mis-configured"""

    # TODO: Service validation
    # * Check through all configurations that we're not messing with port numbers
    # * ???

    _ = ctx

    return True, "VALIDATION_NOT_IMPLEMENTED"


@instance.command(short_help="instance ssl certificate")
@click.option(
    "--selfsigned",
    help="Use a self-signed certificate",
    default=False,
    is_flag=True,
)
@click.pass_context
def cert(ctx, selfsigned):
    """instance a local SSL certificate"""

    instance_configuration = ctx.obj["instance_configuration"]
    instance_name = ctx.obj["instance"]
    next_environment = get_next_environment(ctx)

    set_instance(instance_name, next_environment)

    if selfsigned:
        _instance_selfsigned(instance_configuration)
    else:
        log("This is work in progress")
        abort(55555)

        _instance_letsencrypt(instance_configuration)

    finish(ctx)


def _instance_letsencrypt(instance_configuration):
    hostnames = instance_configuration.get("web_hostnames", False)
    hostnames = hostnames.replace(" ", "")

    if not hostnames or hostnames == "localhost":
        log(
            "Please configure the public fully qualified domain names of this instance.\n"
            "Use 'iso instance set web_hostnames your.hostname.tld' to do that.\n"
            "You can add multiple names by separating them with commas.",
            lvl=error,
        )
        abort(50031)

    contact = instance_configuration.get("contact", False)
    if not contact:
        log(
            "You need to specify a contact mail address for this instance to generate certificates.\n"
            "Use 'iso instance set contact your@address.com' to do that.",
            lvl=error,
        )
        abort(50032)

    success, result = run_process(
        "/",
        [
            "certbot",
            "--nginx",
            "certonly",
            "-m",
            contact,
            "-d",
            hostnames,
            "--agree-tos",
            "-n",
        ],
    )
    if not success:
        log(
            "Error getting certificate:",
            format_result(result),
            pretty=True,
            lvl=error,
        )
        abort(50033)


def _instance_selfsigned(instance_configuration):
    """Generates a snakeoil certificate that has only been self signed"""

    log("Generating self signed certificate/key combination")

    try:
        os.mkdir("/etc/ssl/certs/isomer")
    except FileExistsError:
        pass
    except PermissionError:
        log("Need root (e.g. via sudo) to generate ssl certificate")
        abort(1)

    try:
        from OpenSSL import crypto
    except ImportError:
        log("Need python3-openssl to do this.")
        abort(1)
        return

    def create_self_signed_cert(target):
        """Create a simple self signed SSL certificate"""

        key_file = os.path.join(target, "selfsigned.key")
        cert_file = os.path.join(target, "selfsigned.crt")
        combined_file = os.path.join(target, "selfsigned.pem")

        cert_conf = {k: v for k, v in instance_configuration.items() if
                     k.startswith("web_certificate")}

        log("Certificate data:", cert_conf, pretty=True)

        hostname = instance_configuration.get("web_hostnames", gethostname())
        if isinstance(hostname, list):
            hostname = hostname[0]

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        if os.path.exists(cert_file):
            try:
                certificate = open(cert_file, "rb").read()
                old_cert = crypto.load_certificate(crypto.FILETYPE_PEM, certificate)
                serial = old_cert.get_serial_number() + 1
            except (crypto.Error, OSError) as e:
                log(
                    "Could not read old certificate to increment serial:",
                    type(e),
                    e,
                    exc=True,
                    lvl=warn,
                )
                serial = 1
        else:
            serial = 1

        # create a self-signed certificate
        certificate = crypto.X509()
        certificate.get_subject().C = cert_conf.get("web_certificate_country",
                                                    "EU")
        certificate.get_subject().ST = cert_conf.get("web_certificate_state", "Sol")
        certificate.get_subject().L = cert_conf.get("web_certificate_location", "Earth")
        # noinspection PyPep8
        certificate.get_subject().O = cert_conf.get("web_certificate_issuer", "Unknown")
        certificate.get_subject().OU = cert_conf.get("web_certificate_unit", "Unknown")
        certificate.get_subject().CN = hostname
        certificate.set_serial_number(serial)
        certificate.gmtime_adj_notBefore(0)
        certificate.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        certificate.set_issuer(certificate.get_subject())
        certificate.set_pubkey(k)
        certificate.sign(k, "sha512")

        open(key_file, "wt").write(
            str(crypto.dump_privatekey(crypto.FILETYPE_PEM, k), encoding="ASCII")
        )

        open(cert_file, "wt").write(
            str(
                crypto.dump_certificate(crypto.FILETYPE_PEM, certificate),
                encoding="ASCII",
            )
        )

        open(combined_file, "wt").write(
            str(
                crypto.dump_certificate(crypto.FILETYPE_PEM, certificate),
                encoding="ASCII",
            )
            + str(crypto.dump_privatekey(crypto.FILETYPE_PEM, k), encoding="ASCII")
        )

    location = os.path.join(
        get_etc_instance_path(),
        instance_configuration.get("name")
    )

    create_self_signed_cert(location)

    instance_configuration["web_key"] = os.path.join(location, "selfsigned.key")
    instance_configuration["web_certificate"] = os.path.join(location, "selfsigned.crt")

    write_instance(instance_configuration)


@instance.command(short_help="install systemd service")
@click.pass_context
def service(ctx):
    """instance systemd service configuration"""

    update_service(ctx, ctx.obj["instance_configuration"]["environment"])
    finish(ctx)


@instance.command(short_help="instance nginx configuration")
@click.option(
    "--hostname",
    default=None,
    help="Override public Hostname (FQDN) Default from active system " "configuration",
)
@click.pass_context
def update_nginx(ctx, hostname):
    """instance nginx configuration"""

    ctx.obj["hostname"] = hostname

    _create_nginx_config(ctx)
    finish(ctx)


def _create_nginx_config(ctx):
    """instance nginx configuration"""

    # TODO: Specify template url very precisely. Currently one needs to be in
    #  the repository root

    instance_name = ctx.obj["instance"]
    config = ctx.obj["instance_configuration"]

    current_env = config["environment"]
    env = config["environments"][current_env]

    dbhost = config["database_host"]
    dbname = env["database"]

    hostnames = ctx.obj.get("web_hostnames", None)
    if hostnames is None:
        hostnames = config.get("web_hostnames", None)
    if hostnames is None:
        try:
            configuration = _get_system_configuration(dbhost, dbname)
            hostnames = configuration.hostname
        except Exception as e:
            log("Exception:", e, type(e), exc=True, lvl=error)
            log(
                """Could not determine public fully qualified hostname!
Check systemconfig (see db view and db modify commands) or specify
manually with --hostname host.domain.tld

Using 'localhost' for now""",
                lvl=warn,
            )
            hostnames = "localhost"
    port = config["web_port"]
    address = config["web_address"]

    log(
        "Creating nginx configuration for %s:%i using %s@%s"
        % (hostnames, port, dbname, dbhost)
    )

    definitions = {
        "server_public_name": hostnames.replace(",", " "),
        "ssl_certificate": config["web_certificate"],
        "ssl_key": config["web_key"],
        "host_url": "http://%s:%i/" % (address, port),
        "instance": instance_name,
        "environment": current_env,
    }

    if distribution == "DEBIAN":
        configuration_file = "/etc/nginx/sites-available/isomer.%s.conf" % instance_name
        configuration_link = "/etc/nginx/sites-enabled/isomer.%s.conf" % instance_name
    elif distribution == "ARCH":
        configuration_file = "/etc/nginx/nginx.conf"
        configuration_link = None
    else:
        log(
            "Unsure how to proceed, you may need to specify your " "distribution",
            lvl=error,
        )
        return

    log("Writing nginx Isomer site definition")
    write_template(nginx_template, configuration_file, definitions)

    if configuration_link is not None:
        log("Enabling nginx Isomer site (symlink)")
        if not os.path.exists(configuration_link):
            os.symlink(configuration_file, configuration_link)

    if os.path.exists("/bin/systemctl"):
        log("Restarting nginx service")
        run_process("/", ["systemctl", "restart", "nginx.service"], sudo="root")
    else:
        log("No systemctl found, not restarting nginx")

# TODO: Add instance user
