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
Isomer - Backend

Application
===========

See README.rst for Build/Installation and setup details.

URLs & Contact
==============

Mail: riot@c-base.org
IRC: #hackerfleet@irc.freenode.org

Project repository: http://github.com/isomeric/isomer
Frontend repository: http://github.com/isomeric/isomer-frontend


"""

import grp
import pwd
import sys
import os

import pyinotify
import click
from circuits import Event, Timer
from circuits.web import Server, Static
from circuits.web.websockets.dispatcher import WebSocketsDispatcher

from isomer.misc.path import set_instance, get_path
from isomer.component import handler, ConfigurableComponent, ComponentDisabled, BaseMeta
# from isomer.schemata.component import ComponentBaseConfigSchema
from isomer.database import initialize  # , schemastore
from isomer.events.system import populate_user_events, system_stop
from isomer.logger import (
    isolog,
    verbose,
    debug,
    warn,
    error,
    critical,
    setup_root,
)
from isomer.debugger import cli_register_event
from isomer.ui.builder import install_frontend
from isomer.error import abort, EXIT_NO_CERTIFICATE
from isomer.tool.etc import load_instance
from isomer.provisions import build_provision_store
from isomer.provisions.base import provision


# from circuits.web.errors import redirect
# from circuits.app.daemon import Daemon


# from pprint import pprint


class ready(Event):
    """Event fired to signal completeness of the local node's setup"""

    pass


class boot(Event):
    pass


class cli_components(Event):
    """List registered and running components"""

    pass


class cli_reload_db(Event):
    """Reload database and schemata (Dangerous!) WiP - does nothing right now"""

    pass


class cli_reload(Event):
    """Reload all components and data models"""

    pass


class cli_info(Event):
    """Provide information about the running instance"""

    verbose = False


class cli_quit(Event):
    """Stop this instance

    Uses sys.exit() to quit.
    """

    pass


class cli_drop_privileges(Event):
    """Try to drop possible root privileges"""

    pass


class cli_check_provisions(Event):
    """Check current provisioning state and trigger new provisioning"""

    pass


class FrontendHandler(pyinotify.ProcessEvent):
    def __init__(self, launcher, *args, **kwargs):
        """Initialize the frontend handler"""
        super(FrontendHandler, self).__init__(*args, **kwargs)
        self.launcher = launcher

    def process_IN_CLOSE_WRITE(self, event):
        isolog("Frontend change:", event, emitter="FRONTENDHANDLER")
        install_frontend(install=False, development=True)


def drop_privileges(uid_name="isomer", gid_name="isomer"):
    """Attempt to drop privileges and change user to 'isomer' user/group"""

    if os.getuid() != 0:
        isolog("Not root, cannot drop privileges", lvl=warn, emitter="CORE")
        return

    try:
        # Get the uid/gid from the name
        running_uid = pwd.getpwnam(uid_name).pw_uid
        running_gid = grp.getgrnam(gid_name).gr_gid

        # Remove group privileges
        os.setgroups([])

        # Try setting the new uid/gid
        os.setgid(running_gid)
        os.setuid(running_uid)

        # Ensure a very conservative umask
        # old_umask = os.umask(22)
        isolog("Privileges dropped", emitter="CORE")
    except Exception as e:
        isolog(
            "Could not drop privileges:",
            e,
            type(e),
            exc=True,
            lvl=error,
            emitter="CORE",
        )


class Core(ConfigurableComponent):
    """Isomer Core Backend Application"""

    # TODO: Move most of this stuff over to a new FrontendBuilder

    configprops = {
        "enabled": {
            "type": "array",
            "title": "Available modules",
            "description": "Modules found and activatable by the system.",
            "default": [],
            "items": {"type": "string"},
        },
        "components": {
            "type": "object",
            "title": "Components",
            "description": "Component metadata",
            "default": {},
        },
        "frontendenabled": {
            "type": "boolean",
            "title": "Frontend enabled",
            "description": "Option to toggle frontend activation",
            "default": True,
        },
    }

    def __init__(self, name, instance, **kwargs):
        super(Core, self).__init__("CORE", **kwargs)
        self.log("Starting system (channel ", self.channel, ")")

        self.insecure = kwargs["insecure"]
        self.development = kwargs["dev"]

        self.instance = name

        host = kwargs.get("web_address", None)
        port = kwargs.get("web_port", None)

        # self.log(instance, pretty=True, lvl=verbose)

        self.host = instance["web_address"] if host is None else host
        self.port = instance["web_port"] if port is None else port

        self.log("Web configuration: %s:%i" % (self.host, int(self.port)), lvl=debug)

        self.certificate = certificate = (
            instance["web_certificate"] if instance["web_certificate"] != "" else None
        )

        if certificate:
            if not os.path.exists(certificate):
                self.log(
                    "SSL certificate usage requested but certificate "
                    "cannot be found!",
                    lvl=error,
                )
                abort(EXIT_NO_CERTIFICATE)

        # TODO: Find a way to synchronize this with the paths in i.u.builder
        if self.development:
            self.frontend_root = os.path.abspath(
                os.path.dirname(os.path.realpath(__file__)) + "/../frontend"
            )
            self.frontend_target = get_path("lib", "frontend-dev")
            self.module_root = os.path.abspath(
                os.path.dirname(os.path.realpath(__file__)) + "/../modules"
            )
        else:
            self.frontend_root = get_path("lib", "repository/frontend")
            self.frontend_target = get_path("lib", "frontend")
            self.module_root = ""

        self.log(
            "Frontend & module paths:",
            self.frontend_root,
            self.frontend_target,
            self.module_root,
            lvl=verbose,
        )

        self.modules_loaded = {}
        self.loadable_components = {}
        self.loaded_components = {}

        self.frontend_running = False
        self.frontend_watcher = None
        self.frontend_watch_manager = None

        self.static = None
        self.websocket = None

        self.component_blacklist = instance["environments"][instance["environment"]][
            "blacklist"
        ]

        self.component_blacklist += list(kwargs.get("blacklist", []))

        self._check_provisions()
        self.update_components()
        self._write_config()

        self.server = None

        if self.insecure:
            self.log("Not dropping privileges - this may be insecure!", lvl=warn)

    @handler("started", channel="*")
    def ready(self, source):
        """All components have initialized, set up the component
        configuration schema-store, run the local server and drop privileges"""

        from isomer.schemastore import configschemastore

        configschemastore[self.name] = self.configschema

        self._start_server()

        if not self.insecure:
            self._drop_privileges()

        self.fireEvent(cli_register_event("components", cli_components))
        self.fireEvent(cli_register_event("drop_privileges", cli_drop_privileges))
        self.fireEvent(cli_register_event("check_provisions", cli_check_provisions))
        self.fireEvent(cli_register_event("reload_db", cli_reload_db))
        self.fireEvent(cli_register_event("reload", cli_reload))
        self.fireEvent(cli_register_event("quit", cli_quit))
        self.fireEvent(cli_register_event("info", cli_info))

        self.fireEvent(boot(), "*")

    @handler("frontendbuildrequest", channel="setup")
    def trigger_frontend_build(self, event):
        """Event hook to trigger a new frontend build"""

        install_frontend(
            force_rebuild=event.force,
            install=event.install,
            development=self.development,
        )
        self.log("Frontend install done")

    @handler("cli_drop_privileges")
    def cli_drop_privileges(self, event):
        """Drop possible user privileges"""

        self.log("Trying to drop privileges", lvl=debug)
        self._drop_privileges()

    @handler("cli_check_provisions")
    def cli_check_provisions(self, event):
        """Check current provisioning state and trigger new provisioning"""

        self.log("Checking provisions", lvl=debug)
        self._check_provisions()

    @handler("cli_components")
    def cli_components(self, event):
        """List all loaded and running unique components"""

        self.log("Loaded components: ", sorted(self.loaded_components.keys()))
        self.log("Running unique components: ", sorted(self.names))

    @handler("cli_reload_db")
    def cli_reload_db(self, event):
        """Experimental call to reload the database"""

        self.log("This command is WiP.")

        initialize()

    @handler("cli_reload")
    def cli_reload(self, event):
        """Experimental call to reload the component tree"""

        self.log("Reloading all components.")

        self.update_components(forcereload=True)
        initialize()

        from isomer.debugger import cli_comp_graph

        self.fireEvent(cli_comp_graph())

    @handler("cli_quit")
    def cli_quit(self, event):
        """Stop the instance on cli request"""

        self.log("Quitting on CLI request.")
        if self.frontend_watcher is not None:
            self.frontend_watcher.stop()
            self.frontend_watcher = None

        if self.context.params["dev"] is False:
            self.fireEvent(system_stop())
        else:
            self.log("Stopping immediately due to --dev flag", lvl=warn)
            self.stop_core(None)

    @handler("system_stop")
    def system_stop(self):
        """Stop instance after settling stop events"""

        self.log("Initiating stop")
        Timer(5, Event.create("stop_core")).register(self)

    @handler("signal", channel="*")
    def _on_signal(self, signo, stack):
        """Handle abort signals"""
        if signo in [2, 15]:
            self.log("Initiating stop")
            Timer(5, Event.create("stop_core")).register(self)

    @handler("stop_core")
    def stop_core(self, event):
        """Stop execution and exit"""

        self.log("Stopping execution.")
        self.log("Source:", event, lvl=verbose)

        self.stop()
        sys.exit()

    @handler("cli_info")
    def cli_info(self, *args):
        """Provides information about the running instance"""

        from isomer.database import dbname, dbhost, dbport

        self.log(
            "Instance: %s DB: %s Dev: %s Host: %s Port: %s Insecure: %s Frontend: %s\n"
            "Modules:"
            % (
                self.instance,
                "%s@%s:%i" % (dbname, dbhost, dbport),
                self.development,
                self.host,
                self.port,
                self.insecure,
                self.frontend_target,
            ),
            self.modules_loaded,
            pretty=True,
        )

        if "-v" in args:
            self.log("Context:", self.context.obj, pretty=True)

    def _start_server(self):
        """Run the node local server"""

        self.log("Starting server")
        secure = self.certificate is not None
        if secure:
            self.log("Running SSL server with cert:", self.certificate)
        else:
            self.log(
                "Running insecure server without SSL. Do not use without SSL "
                "proxy in production!",
                lvl=warn,
            )

        try:
            self.server = Server(
                (self.host, self.port),
                display_banner=False,
                secure=secure,
                certfile=self.certificate  # ,
                # inherit=True
            ).register(self)
        except PermissionError as e:
            if self.port <= 1024:
                self.log(
                    "Could not open privileged port (%i), check permissions!"
                    % self.port,
                    e,
                    lvl=critical,
                )
            else:
                self.log("Could not open port (%i):" % self.port, e, lvl=critical)
        except OSError as e:
            if e.errno == 98:
                self.log("Port (%i) is already opened!" % self.port, lvl=critical)
            else:
                self.log("Could not open port (%i):" % self.port, e, lvl=critical)

    def _drop_privileges(self, *args):
        self.log("Dropping privileges", lvl=debug)
        drop_privileges()

    # Moved to manage tool, maybe of interest later, though:
    #
    # @handler("componentupdaterequest", channel="setup")
    # def trigger_component_update(self, event):
    #     self.update_components(forcereload=event.force)

    def update_components(
            self, forcereload=False, forcerebuild=False, forcecopy=True, install=False
    ):
        """Check all known entry points for components. If necessary,
        manage configuration updates"""

        # TODO: See if we can pull out major parts of the component handling.
        #  They are also used in the manage-tool to instantiate the
        #  component frontend bits.

        self.log("Updating components")
        components = {}
        packages = {}

        try:

            from pkg_resources import iter_entry_points

            entry_point_tuple = (
                iter_entry_points(group="isomer.base", name=None),
                iter_entry_points(group="isomer.sails", name=None),
                iter_entry_points(group="isomer.components", name=None),
            )
            self.log("Entrypoints:", entry_point_tuple, pretty=True, lvl=verbose)
            for iterator in entry_point_tuple:
                for entry_point in iterator:
                    self.log("Entrypoint:", entry_point, pretty=True, lvl=verbose)
                    try:
                        name = entry_point.name
                        package = entry_point.dist.project_name
                        version = str(entry_point.dist.parsed_version)
                        location = entry_point.dist.location
                        loaded = entry_point.load()

                        self.log(
                            "Entry point: ",
                            entry_point,
                            name,
                            entry_point.resolve(),
                            lvl=verbose,
                        )

                        module_name = location.split("/")[-1]
                        if module_name in self.modules_loaded:
                            self.modules_loaded[module_name].append(name)
                        else:
                            self.modules_loaded[module_name] = [name]

                        self.log("Loaded: ", loaded, lvl=verbose)
                        comp = {
                            "package": package,
                            "location": location,
                            "version": version,
                            "description": loaded.__doc__,
                        }

                        components[name] = comp
                        self.loadable_components[name] = loaded

                        packages.setdefault(
                            package, {"version": version, "name": package}
                        )

                        self.log("Loaded component:", comp, lvl=verbose)

                    except Exception as e:
                        self.log(
                            "Could not inspect entrypoint: ",
                            e,
                            type(e),
                            entry_point,
                            iterator,
                            lvl=error,
                            exc=True,
                        )

                        # for name in components.keys():
                        #     try:
                        #         self.log(self.loadable_components[name])
                        #         configobject = {
                        #             'type': 'object',
                        #             'properties':
                        # self.loadable_components[name].configprops
                        #         }
                        #         ComponentBaseConfigSchema['schema'][
                        # 'properties'][
                        #             'settings'][
                        #             'oneOf'].append(configobject)
                        #     except (KeyError, AttributeError) as e:
                        #         self.log('Problematic configuration
                        # properties in '
                        #                  'component ', name, exc=True)
                        #
                        # schemastore['component'] = ComponentBaseConfigSchema

        except Exception as e:
            self.log("Component update error: ", e, type(e), lvl=error, exc=True)
            return

        from isomer.database import objectmodels

        systemconfig = objectmodels["systemconfig"].find_one({"active": True})

        systemconfig.packages = sorted(list(packages.values()), key=lambda x: x["name"])
        systemconfig.save()

        # self.log(list(packages.values()), lvl=critical)

        self.log(
            "Checking component frontend bits in ", self.frontend_root, lvl=verbose
        )

        # pprint(self.config._fields)
        diff = set(components) ^ set(self.config.components)
        if diff or forcecopy and self.config.frontendenabled:
            self.log("Old component configuration differs:", diff, lvl=debug)
            self.log(self.config.components, components, lvl=verbose)
            self.config.components = components
        else:
            self.log("No component configuration change. Proceeding.")

        if forcereload:
            self.log("Restarting all components.", lvl=warn)
            self._instantiate_components(clear=True)

    def _start_frontend(self, restart=False):
        """Check if it is enabled and start the frontend http & websocket"""

        self.log(self.config, self.config.frontendenabled, lvl=verbose)
        if self.config.frontendenabled and not self.frontend_running or restart:
            self.log("Restarting webfrontend services on", self.frontend_target)

            self.static = Static("/", docroot=self.frontend_target).register(self)
            self.websocket = WebSocketsDispatcher("/websocket").register(self)
            self.frontend_running = True

            if self.development:
                self.frontend_watch_manager = pyinotify.WatchManager()
                self.frontend_watcher = pyinotify.ThreadedNotifier(
                    self.frontend_watch_manager, FrontendHandler(self)
                )
                self.frontend_watcher.start()
                # noinspection PyUnresolvedReferences
                mask = (
                        pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
                )
                self.log("Frontend root:", self.frontend_root, lvl=debug)
                self.frontend_watch_manager.add_watch(self.module_root, mask, rec=True)

    def _check_provisions(self):
        from isomer.database import objectmodels

        systemconfig = objectmodels["systemconfig"].find_one({"active": True})

        if systemconfig is None:
            self.log("No system configuration found, trying tp provision", lvl=warn)
            provision()
        else:
            provisioned_packages = set(systemconfig.provisions["packages"])
            provision_store = set(build_provision_store().keys())
            missing_provisions = provision_store - provisioned_packages
            self.log("Provisioned packages:", provisioned_packages, lvl=debug)
            self.log("Available provisions:", provision_store, lvl=debug)
            if len(missing_provisions) > 0:
                self.log("Installing missing provisions:", missing_provisions)
                provision(installed=provisioned_packages)

    def _instantiate_components(self, clear=True):
        """Inspect all loadable components and run them"""

        if clear:
            # import objgraph
            # from copy import deepcopy
            from circuits.tools import kill
            from circuits import Component

            for comp in self.loaded_components.values():
                self.log(comp, type(comp), isinstance(comp, Component), pretty=True)
                kill(comp)
            # removables = deepcopy(list(self.runningcomponents.keys()))
            #
            # for key in removables:
            #     comp = self.runningcomponents[key]
            #     self.log(comp)
            #     comp.unregister()
            #     comp.stop()
            #     self.runningcomponents.pop(key)
            #
            #     objgraph.show_backrefs([comp],
            #                            max_depth=5,
            #                            filter=lambda x: type(x) not in [list, tuple, set],
            #                            highlight=lambda x: type(x) in [ConfigurableComponent],
            #                            filename='backref-graph_%s.png' % comp.uniquename)
            #     del comp
            # del removables
            self.loaded_components = {}

        self.log(
            "Not running blacklisted components: ", self.component_blacklist, lvl=debug
        )

        running = set(self.loadable_components.keys()).difference(
            self.component_blacklist
        )
        self.log("Starting components: ", sorted(running))
        for name, componentdata in self.loadable_components.items():
            if name in self.component_blacklist:
                continue
            self.log("Running component: ", name, lvl=debug)
            try:
                if name in self.loaded_components:
                    self.log("Component already running: ", name, lvl=warn)
                else:
                    try:
                        runningcomponent = componentdata()
                    except ComponentDisabled:
                        self.log("Not registering disabled component", lvl=debug)
                        continue

                    runningcomponent.register(self)
                    self.loaded_components[name] = runningcomponent
            except Exception as e:
                self.log(
                    "Could not register component: ",
                    name,
                    e,
                    type(e),
                    lvl=error,
                    exc=True,
                )

    def started(self, component):
        """Sets up the application after startup."""

        self.log("Running.")
        self.log("Started event origin: ", component, lvl=verbose)
        populate_user_events()

        from isomer.events.system import AuthorizedEvents

        self.log(
            len(AuthorizedEvents),
            "authorized event sources:",
            list(AuthorizedEvents.keys()),
            lvl=debug,
        )

        self._instantiate_components()
        self._start_frontend()
        self.fire(ready(), "isomer-web")


def construct_graph(ctx, name, instance, args):
    """Preliminary Isomer application Launcher"""

    app = Core(name, instance, **args)

    # TODO: This should probably be read-only
    BaseMeta.context = ctx

    setup_root(app)

    if args["debug"]:
        from circuits import Debugger

        isolog("Starting circuits debugger", lvl=warn, emitter="GRAPH")
        dbg = Debugger().register(app)
        # TODO: Make these configurable from modules, navdata is _very_ noisy
        # but should not be listed _here_
        dbg.IgnoreEvents.extend(
            [
                "read",
                "_read",
                "write",
                "_write",
                "stream_success",
                "stream_complete",
                "serial_packet",
                "raw_data",
                "stream",
                "navdatapush",
                "referenceframe",
                "updateposition",
                "updatesubscriptions",
                "generatevesseldata",
                "generatenavdata",
                "sensordata",
                "reset_flood_offenders",
                "reset_flood_counters",  # Flood counters
                "task_success",
                "task_done",  # Thread completion
                "keepalive",  # IRC Gateway
                "peek",  # AVIO and others
                "joystickchange",  # AVIO
            ]
        )

    isolog("Beginning graph assembly.", emitter="GRAPH")

    if args["draw_graph"]:
        from circuits.tools import graph

        graph(app)

    if args["open_gui"]:
        import webbrowser

        # TODO: Fix up that url:
        webbrowser.open("http://%s:%i/" % (args["host"], args["port"]))

    isolog("Graph assembly done.", emitter="GRAPH")

    return app


@click.command()
@click.option(
    "--web-port", "-p", help="Define port for UI server", type=int, default=None
)
@click.option(
    "--web-address",
    "-a",
    help="Define listening address for UI server",
    type=str,
    default=None,
)
@click.option(
    "--web-certificate", "-c", help="Certificate file path", type=str, default=None
)
@click.option("--profile", help="Enable profiler", is_flag=True)
@click.option(
    "--open-gui",
    help="Launch web browser for GUI inspection after startup",
    is_flag=True,
)
@click.option(
    "--draw-graph",
    help="Draw a snapshot of the component graph after construction",
    is_flag=True,
)
@click.option("--live-log", help="Log to in-memory structure as well", is_flag=True)
@click.option("--debug", help="Run circuits debugger", is_flag=True)
@click.option("--dev", help="Run development server", is_flag=True, default=False)
@click.option("--insecure", help="Keep privileges - INSECURE", is_flag=True)
@click.option("--no-run", "-n", help="Only assemble system, do not run", is_flag=True)
@click.option(
    "--blacklist",
    "-b",
    help="Blacklist a component (can be repeated)",
    multiple=True,
    default=[],
)
@click.pass_context
def launch(ctx, run=True, **args):
    """Assemble and run an Isomer instance"""

    instance_name = ctx.obj["instance"]
    instance = load_instance(instance_name)
    environment_name = ctx.obj["environment"]

    isolog(
        "Launching instance %s - (%s)" % (instance_name, environment_name),
        emitter="CORE",
        lvl=debug
    )

    database_host = ctx.obj["dbhost"]
    database_name = ctx.obj["dbname"]

    if ctx.params["live_log"] is True:
        from isomer import logger

        logger.live = True

    if args["web_certificate"] is not None:
        isolog(
            "Warning! Using SSL on the backend is currently not recommended!",
            lvl=critical,
            emitter="CORE",
        )

    isolog("Initializing database access", emitter="CORE", lvl=debug)
    initialize(database_host, database_name, instance_name)
    isolog("Setting instance paths", emitter="CORE", lvl=debug)
    set_instance(instance_name, environment_name)

    server = construct_graph(ctx, instance_name, instance, args)
    if run and not args["no_run"]:
        server.run()

    return server
