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

Test Isomer Client Manager
==========================



"""

import pytest
from circuits import Manager
from circuits.net.events import read  # , write
from json import dumps  # , loads

from isomer.ui.clientmanager import ClientManager
from isomer.ui.clientobjects import Client, Socket
from isomer.events.client import clientdisconnect
from isomer.misc.std import std_uuid

from pprint import pprint

m = Manager()

cm = ClientManager()
cm.register(m)


def test_instantiate():
    """Tests correct instantiation"""

    assert type(cm) == ClientManager


def transmit(event_in, channel_in, event_out, channel_out):
    """Fire an event and listen for a reply"""

    waiter = pytest.WaitEvent(m, event_in, channel_in)

    m.fire(event_out, channel_out)

    result = waiter.wait()

    return result


def test_auth_request():
    """Test if clientmanager fires an authentication-request on login"""

    m.start()

    # TODO: Rebuild this, to actually connect a fake socket via cm.connect(socket, IP)

    uuid = std_uuid()
    socket = Socket('127.0.0.1', uuid)
    cm._sockets[socket] = socket

    data = {
        'component': 'auth',
        'action': 'login',
        'data': {
            'username': 'foo',
            'password': 'bar'
        }
    }

    event = read(socket, dumps(data))

    result = transmit('authenticationrequest', 'auth', event, 'wsserver')

    assert result.username == 'foo'
    assert result.password == 'bar'


def test_auto_auth_request():
    """Tests if automatic authentication requests work"""

    m.start()
    # TODO: Rebuild this, to actually connect a fake socket via cm.connect(socket, IP)

    uuid = std_uuid()
    socket = Socket('127.0.0.1', uuid)
    cm._sockets[socket] = socket

    client_config_uuid = std_uuid()

    data = {
        'component': 'auth',
        'action': 'autologin',
        'data': {
            'uuid': client_config_uuid

        }
    }

    event = read(socket, dumps(data))

    result = transmit('authenticationrequest', 'auth', event, 'wsserver')

    pprint(result.__dict__)
    assert result.auto is True
    assert result.requestedclientuuid['uuid'] == client_config_uuid


def test_auth_logout():

    client_uuid = std_uuid()
    user_uuid = std_uuid()

    cm._clients[client_uuid] = Client(None, '127.0.0.1', client_uuid, user_uuid, 'TESTER')

    m.start()

    cm._handle_authentication_events(None, 'logout', client_uuid, None)

    data = {
        'component': 'auth',
        'action': 'logout',
        'data': {}
    }

    event = read(None, dumps(data))

    result = transmit('clientdisconnect', 'isomer-web', event, 'wsserver')

    assert result.clientuuid == client_uuid
    assert isinstance(result, clientdisconnect)

