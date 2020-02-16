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

import os
import sys
import shutil
import threading
import collections

import pytest
import pymongo
from time import sleep, strftime
from collections import deque
from click.testing import CliRunner

from circuits.core.manager import TIMEOUT
from circuits import handler, BaseComponent, Debugger, Manager

from formal import model_factory

from isomer.database import initialize
from isomer.component import ConfigurableComponent
from isomer.misc.path import set_etc_path, set_instance
from isomer.schemata.component import ComponentConfigSchemaTemplate

"""Basic Test suite bits and pieces"""

DEFAULT_DATABASE_NAME = "isomer-test-internal"
DEFAULT_DATABASE_HOST = "localhost"
DEFAULT_DATABASE_PORT = "27017"
COLORS = False


class TestComponent(ConfigurableComponent):
    """Very basic testing component"""

    configprops = {
        'test': {'type': 'string'}
    }


class Watcher(BaseComponent):
    """Watches for incoming events"""

    def __init__(self, *args, **kwargs):
        super(Watcher).__init__(*args, **kwargs)
        self.events = deque()
        self._lock = threading.Lock()

    @handler(channel="*", priority=999.9)
    def _on_event(self, event, *args, **kwargs):
        with self._lock:
            self.events.append(event)

    def clear(self):
        """Reset caught events"""

        self.events.clear()

    def wait(self, name, channel=None, timeout=6.0):
        """Linger and wait for specified incoming events"""

        for i in range(int(timeout / TIMEOUT)):
            with self._lock:
                for event in self.events:
                    if event.name == name and event.waitingHandlers == 0:
                        if (channel is None) or (channel in event.channels):
                            return True
            sleep(TIMEOUT)
        else:
            return False


class Flag(object):
    """Flag object for Watcher component"""
    status = False
    event = None


def call_event_from_name(manager, event, event_name, *channels):
    """Fire a named event and wait for a specified response"""

    fired = False
    value = None
    for r in manager.waitEvent(event_name):
        if not fired:
            fired = True
            value = manager.fire(event, *channels)
        sleep(0.1)
    return value


def call_event(manager, event, *channels):
    """Simply fire and forget a specified event"""

    return call_event_from_name(manager, event, event.name, *channels)


class WaitEvent(object):
    """Simple component substitute that waits for a specified Event"""

    def __init__(self, manager, name, channel=None, timeout=1.0):
        if channel is None:
            channel = getattr(manager, "channel", None)

        self.timeout = timeout
        self.manager = manager

        flag = Flag()

        @handler(name, channel=channel)
        def on_event(self, event):
            """An event has been received"""

            flag.status = True
            flag.event = event

        self.handler = self.manager.addHandler(on_event)
        self.flag = flag

    def wait(self):
        """Wait for the (upon instantiation) specified timeout for an event"""
        try:
            for i in range(int(self.timeout / TIMEOUT)):
                if self.flag.status:
                    return self.flag.event
                sleep(TIMEOUT)
        finally:
            self.manager.removeHandler(self.handler)


def wait_for(obj, attr, value=True, timeout=3.0):
    """Wait until timeout or an object acquires a specified attribute"""

    from circuits.core.manager import TIMEOUT
    for i in range(int(timeout / TIMEOUT)):
        if isinstance(value, collections.Callable):
            if value(obj, attr):
                return True
        elif getattr(obj, attr) == value:
            return True
        sleep(TIMEOUT)


@pytest.fixture
def manager(request):
    """Component testing manager/fixture"""

    manager = Manager()

    def finalizer():
        """Stop the testing"""

        manager.stop()

    request.addfinalizer(finalizer)

    waiter = WaitEvent(manager, "started")
    manager.start()
    assert waiter.wait()

    if request.config.option.verbose:
        verbose = True
    else:
        verbose = False

    Debugger(events=verbose).register(manager)

    return manager


@pytest.fixture
def watcher(request, manager):
    """Fixture that cleans up after unregistering"""

    watcher = Watcher().register(manager)

    def finalizer():
        """Setup the manager and wait for completion, then unregister"""

        waiter = WaitEvent(manager, "unregistered")
        watcher.unregister()
        waiter.wait()

    request.addfinalizer(finalizer)

    return watcher


def run_cli(cmd, args, full_log=False):
    """Runs a command"""

    if COLORS is False:
        args.insert(0, '-nc')

    if full_log:
        timestamp = strftime("%Y%m%d-%H%M%S")

        log_args = [
            '--clog', '5', '--flog', '5',
            '--log-file', '/tmp/isomer-test_%s' % timestamp
        ]
        args = log_args + args

    args = ['--config-path', '/tmp/isomer-test/etc/isomer'] + args

    # pprint(args)

    runner = CliRunner()
    result = runner.invoke(cmd, args, catch_exceptions=False, obj={})
    with open('/tmp/logfile_runner', 'a') as f:
        f.write(result.output)
    return result


def reset_base():
    """Prepares a testing folder and sets Isomer's base to that"""
    if os.path.exists('/tmp/isomer-test'):
        shutil.rmtree('/tmp/isomer-test')

    os.makedirs('/tmp/isomer-test/etc/isomer/instances')
    os.makedirs('/tmp/isomer-test/var/log/isomer')

    set_etc_path('/tmp/isomer-test/etc/isomer')
    set_instance('foobar', 'green', '/tmp/isomer-test/')


def clean_test_components():
    """Removes test-generated component data"""

    print("Removing test components...")
    for item in model_factory(ComponentConfigSchemaTemplate).find({
        'componentclass': 'TestComponent'
    }):
        item.delete()


def clean_test_database(config):
    """Removes all of the test-generated database content"""

    db_name = config.getoption("--dbname", default=DEFAULT_DATABASE_NAME)
    host = config.getoption("--dbhost", default=DEFAULT_DATABASE_HOST)
    port = config.getoption("--dbport", default=DEFAULT_DATABASE_PORT)

    client = pymongo.MongoClient(host=host, port=int(port))
    if db_name in client.list_database_names():
        print("Dropping test database", db_name)
        client.drop_database(db_name)
    else:
        print("Test database does not exist")


@pytest.hookimpl()
def pytest_unconfigure(config):
    """Clear test generated data after test completion"""

    clean_test_database(config)


def pytest_addoption(parser):
    parser.addoption(
        "--dbname", action="store", default=DEFAULT_DATABASE_NAME, help="test db name"
    )
    parser.addoption(
        "--dbhost", action="store", default=DEFAULT_DATABASE_HOST, help="test db hostname"
    )
    parser.addoption(
        "--dbport", action="store", default=DEFAULT_DATABASE_PORT, help="test db port"
    )


def pytest_configure(config):
    """Setup the testing namespace"""

    dbname = config.getoption("--dbname", default=DEFAULT_DATABASE_NAME)
    dbhost = config.getoption("--dbhost", default=DEFAULT_DATABASE_HOST)
    dbport = config.getoption("--dbport", default=DEFAULT_DATABASE_PORT)

    pytest.TestComponent = TestComponent
    pytest.clean_test_components = clean_test_components
    pytest.WaitEvent = WaitEvent
    pytest.wait_for = wait_for
    pytest.call_event = call_event
    pytest.PLATFORM = sys.platform
    pytest.PYVER = sys.version_info[:3]
    pytest.DBNAME = dbname
    pytest.DBHOST = dbhost
    pytest.DBPORT = dbport
    pytest.call_event_from_name = call_event_from_name
    pytest.run_cli = run_cli
    pytest.reset_base = reset_base

    clean_test_database(config)

    initialize(database_name=dbname)
