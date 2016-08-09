"""


Module: Events
==============

Major HFOS event declarations

:copyright: (C) 2011-2016 riot@hackerfleet.org
:license: GPLv3 (See LICENSE)

"""

from circuits.core import Event

from hfos.logger import hfoslog, critical, events
from hfos.ui.clientobjects import User

__author__ = "Heiko 'riot' Weinen <riot@hackerfleet.org>"


class authorizedevent(Event):
    """Base class for events for logged in users."""

    def __init__(self, user, action, data, client, *args):
        """
        Sets up an authorized event.

        :param user: User object from :py:class:hfos.web.clientmanager.User
        :param action:
        :param data:
        :param client:
        :param args:
        :return:
        """

        assert isinstance(user, User)

        super(authorizedevent, self).__init__(*args)
        self.user = user
        self.action = action
        self.data = data
        self.client = client


# Authenticator Events

class profilerequest(authorizedevent):
    """A user has changed his profile"""

    def __init__(self, *args):
        """

        :param user: Userobject of client
        :param data: The new profile data
        """
        super(profilerequest, self).__init__(*args)

        hfoslog("[PROFILE-EVENT] Profile update request: ", self.__dict__,
                lvl=events)


# Schemata requests

class schemarequest(authorizedevent):
    """A client requires a schema to validate data or display a form"""


# Object Management

class objectevent(Event):
    """A unspecified objectevent"""

    def __init__(self, uuid, schema, *args, **kwargs):
        super(objectevent, self).__init__(*args, **kwargs)

        self.uuid = uuid
        self.schema = schema

        hfoslog("[OBJECT-EVENT] Object event created: ", self.__doc__,
                self.__dict__, lvl=events)


class objectchange(objectevent):
    """A stored object has been successfully modified"""


class objectcreation(objectevent):
    """A new object has been successfully created"""


class objectdeletion(objectevent):
    """A stored object has been successfully deleted"""


# Backend-side object change

class updatesubscriptions(objectevent):
    """A backend component needs to write changes to an object.
    Clients that are subscribed should be notified etc.
    """

    def __init__(self, data, *args, **kwargs):
        super(updatesubscriptions, self).__init__(*args, **kwargs)

        self.data = data


class objectmanagerrequest(authorizedevent):
    """A client requires a schema to validate data or display a form"""


# Frontend assembly events

class frontendbuildrequest(Event):
    def __init__(self, force=False, install=False, *args):
        super(frontendbuildrequest, self).__init__(*args)
        self.force = force
        self.install = install


class componentupdaterequest(frontendbuildrequest):
    pass


# Debugger

class logtailrequest(authorizedevent):
    pass


class debugrequest(authorizedevent):
    """Debugging event"""

    def __init__(self, *args):
        super(debugrequest, self).__init__(*args)

        hfoslog('[DEBUG-EVENT] CREATED.', lvl=critical)


AuthorizedEvents = {
    'debugger': debugrequest,
    'objectmanager': objectmanagerrequest,
    'profile': profilerequest,
    'schema': schemarequest,
}