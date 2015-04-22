"""
Hackerfleet Operating System - Backend

Module: Chat
============

Chat manager

:copyright: (C) 2011-2015 riot@hackerfleet.org
:license: GPLv3 (See LICENSE)

"""

__author__ = "Heiko 'riot' Weinen <riot@hackerfleet.org>"

import json

from circuits import Component

from hfos.logger import hfoslog, error, warn, critical

from hfos.events import remotecontrolupdate, send

from time import time


class RemoteControlManager(Component):
    """
    Remote Control manager

    Handles
    * incoming remote control messages
    """

    channel = "hfosweb"

    def __init__(self, *args):
        super(RemoteControlManager, self).__init__(*args)

        self.remotecontroller = None

        hfoslog("RMTCTRL: Started")

    def clientdisconnect(self, event):
        try:
            if event.clientuuid == self.remotecontroller:
                hfoslog("RMTRCTRL: Remote controller disconnected!", lvl=critical)
                self.remotecontroller = None
        except Exception as e:
            hfoslog("RMTRCTRL: Strange thing while client disconnected", e, type(e))

    def remotecontrolrequest(self, event):
        """Remote control event handler for incoming events"""

        hfoslog("RMTCTRL: Event: '%s'" % event.__dict__)
        try:
            action = event.action
            data = event.data
            username = event.user.account.username
            clientname = event.client.name
            clientuuid = event.client.clientuuid

            if action == "takeControl":
                hfoslog("Client wants to remote control: ", username, clientname, lvl=warn)
                if not self.remotecontroller:
                    hfoslog("Success!")
                    self.remotecontroller = clientuuid
                    self.fireEvent(send(clientuuid, {'component': 'remotectrl', 'action': 'takeControl', 'data': True}))
                else:
                    hfoslog("No, we're already being remote controlled!")
                    self.fireEvent(
                        send(clientuuid, {'component': 'remotectrl', 'action': 'takeControl', 'data': False}))
                return
            elif action == "leaveControl":

                if self.remotecontroller == event.client.clientuuid:
                    hfoslog("RMTCTRL: Client leaves control!", username, clientname, lvl=warn)
                    self.remotecontroller = None
                    self.fireEvent(
                        send(clientuuid, {'component': 'remotectrl', 'action': 'takeControl', 'data': False}))
                return
            elif action == "controlData":
                hfoslog("RMTCTRL: Control data received: ", data)
                if event.client.clientuuid == self.remotecontroller:
                    hfoslog("RMTCTRL: Valid data, handing on to ControlDataManager.")
                    self.fireEvent(remotecontrolupdate(data), "remotecontrol")
                else:
                    hfoslog("RMTCTRL: Invalid control data update request!", lvl=warn)

        except Exception as e:
            hfoslog("RMTCTRL: Error: '%s' %s" % (e, type(e)), lvl=error)