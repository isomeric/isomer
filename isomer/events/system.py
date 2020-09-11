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


Module: Events
==============

Major Isomer event declarations


"""

from typing import Dict

from circuits.core import Event
from isomer.logger import isolog, events

# from isomer.ui.clientobjects import User

AuthorizedEvents: Dict[str, Event] = {}
AnonymousEvents: Dict[str, Event] = {}


def get_user_events():
    """Return all registered authorized events"""

    return AuthorizedEvents


def get_anonymous_events():
    """Return all registered anonymous events"""

    return AnonymousEvents


def populate_user_events():
    """Generate a list of all registered authorized and anonymous events"""

    global AuthorizedEvents
    global AnonymousEvents

    def inheritors(klass):
        """Find inheritors of a specified object class"""

        subclasses = {}
        subclasses_set = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses_set:
                    # pprint(child.__dict__)
                    name = child.__module__ + "." + child.__name__

                    subclasses_set.add(child)
                    event = {
                        "event": child,
                        "name": name,
                        "doc": child.__doc__,
                        "args": [],
                    }

                    if child.__module__ in subclasses:
                        subclasses[child.__module__][child.__name__] = event
                    else:
                        subclasses[child.__module__] = {child.__name__: event}
                    work.append(child)
        return subclasses

    # TODO: Change event system again, to catch authorized (i.e. "user") as
    # well as normal events, so they can be processed by Automat

    # NormalEvents = inheritors(Event)
    AuthorizedEvents = inheritors(authorized_event)
    AnonymousEvents = inheritors(anonymous_event)

    # AuthorizedEvents.update(NormalEvents)


class isomer_basic_event(Event):
    """Basic Isomer event class"""

    def __init__(self, *args, **kwargs):
        """Initializes a basic Isomer event.

        For further details, check out the circuits documentation.
        """
        super(isomer_basic_event, self).__init__(*args, **kwargs)


class isomer_ui_event(isomer_basic_event):
    """Isomer user interface event class"""

    pass


class isomer_event(isomer_basic_event):
    """Isomer internal event class"""

    pass


class anonymous_event(isomer_ui_event):
    """Base class for events for logged in users."""

    def __init__(self, action, data, client, *args):
        """
        Initializes an Isomer anonymous user interface event.

        :param action:
        :param data:
        :param client:
        :param args:
        :return:
        """

        self.name = self.__module__ + "." + self.__class__.__name__
        super(anonymous_event, self).__init__(*args)
        self.action = action
        self.data = data
        self.client = client
        isolog("AnonymousEvent created:", self.name, lvl=events)

    @classmethod
    def realname(cls):
        """Return real name of an object class"""

        # For circuits manager to enable module/event namespaces
        return cls.__module__ + "." + cls.__name__


class authorized_event(isomer_ui_event):
    """Base class for events for logged in users."""

    roles = ["admin", "crew"]

    def __init__(self, user, action, data, client, *args):
        """
        Initializes an Isomer authorized user interface event.

        :param user: User object from :py:class:isomer.web.clientmanager.User
        :param action:
        :param data:
        :param client:
        :param args:
        :return:
        """

        # assert isinstance(user, User)

        self.name = self.__module__ + "." + self.__class__.__name__
        super(authorized_event, self).__init__(*args)
        self.user = user
        self.action = action
        self.data = data
        self.client = client
        isolog("AuthorizedEvent created:", self.name, lvl=events)

    @classmethod
    def realname(cls):
        """Return real name of an object class"""

        # For circuits manager to enable module/event namespaces
        return cls.__module__ + "." + cls.__name__

    @classmethod
    def source(cls):
        """Return real name of an object class"""

        # For circuits manager to enable module/event namespaces
        return cls.__module__


class system_stop(isomer_event):
    """Stop everything, save persistent state and cease operations"""


# Configuration reload event

# TODO: This should probably not be an ui-event
class reload_configuration(isomer_ui_event):
    """Instructs a component to reload its configuration"""

    def __init__(self, target, *args, **kwargs):
        super(reload_configuration, self).__init__(*args, **kwargs)
        self.target = target
        isolog("Reload of configuration triggered", lvl=events)


# Authenticator Events


class profilerequest(authorized_event):
    """A user has changed his profile"""

    def __init__(self, *args):
        """

        :param user: Userobject of client
        :param data: The new profile data
        """
        super(profilerequest, self).__init__(*args)

        isolog(
            "Profile update request: ",
            self.__dict__,
            lvl=events,
            emitter="PROFILE-EVENT",
        )


# Frontend assembly events


class frontendbuildrequest(Event):
    """Rebuild and/or install the frontend"""

    def __init__(self, force=False, install=False, *args):
        super(frontendbuildrequest, self).__init__(*args)
        self.force = force
        self.install = install


class componentupdaterequest(frontendbuildrequest):
    """Check for updated components"""

    pass


# Debugger


class logtailrequest(authorized_event):
    """Request the logger's latest output"""

    pass


class debugrequest(authorized_event):
    """Debugging event"""

    def __init__(self, *args):
        super(debugrequest, self).__init__(*args)

        isolog("Created debugrequest", lvl=events, emitter="DEBUG-EVENT")
