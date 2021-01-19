import sys
from json import dumps, loads

from circuits import handler, Timer, Event
from circuits.io import stdin
from circuits.net.events import write
from circuits.web.websockets import WebSocketClient

from isomer.component import LoggingComponent
from isomer.logger import error, verbose, debug, set_verbosity
from isomer.events.system import isomer_event


class get_data(isomer_event):
    def __init__(self, schema, search_filter):
        super(get_data, self).__init__()
        self.schema = schema
        self.search_filter = search_filter


class call_loop(isomer_event):
    pass


class IsomerClient(LoggingComponent):
    def __init__(self, no_stdin=False, no_stdout=False, loop_function=None, loop_frequency=60, *args, **kwargs):
        super(IsomerClient, self).__init__(*args, **kwargs)
        self.url = '{protocol}://{host}:{port}/{url}'.format(**kwargs)
        if no_stdout:
            set_verbosity(100)

        if not no_stdin:
            self.log("Connecting stdin")
            stdin.register(self)

        self.log("Connecting to isomer instance at", self.url)
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')

        self.max_length = 100
        self._request_id = 0

        self.messages = []
        self.hooks = {}

        self.client = WebSocketClient(self.url).register(self)

        if loop_function is not None:
            self.log('Registering external loop function')
            self.loop_function = loop_function
            self.loop_timer = Timer(1/loop_frequency, call_loop(), persist=True).register(self)

        self.log("Ready")

    @handler("call_loop")
    def call_loop(self, event):
        """Runs a given client loop for interactive processes"""
        self.log('Running external loop')
        try:
            self.loop_function()
        except Exception:
            self.loop_timer.unregister()
            Timer(2, Event.create("quit")).register(self)

    @handler("quit")
    def quit(self):
        self.log("Quitting")
        sys.exit()

    @handler("registered")
    def registered(self, event, *args):
        if 'ws' not in event.channels:
            self.log("Hello", event)
            return
        self.log('Transmitting login')

        self.fireEvent(write(""), "ws")

        packet = {
            'component': 'auth',
            'action': 'login',
            'data': {
                'username': self.username,
                'password': self.password
            }
        }

        self._transmit(packet)

    def _transmit(self, packet):

        self.log(packet)
        unicode = dumps(packet).encode('utf-8')
        self.log(unicode, type(unicode))

        self.fireEvent(write(bytes(unicode)), 'ws')

    @handler("read")
    def read(self, *args):
        self.log("Reading")
        msg = args[0]
        self._handle_message(msg)

        self.messages.append(msg)
        if len(msg) > self.max_length:
            msg = str(msg)[:self.max_length] + " ..."
        self.log("Response [%i]: %s" % (len(self.messages), msg))

    def _handle_message(self, msg):
        try:
            decoded = loads(msg)
        except Exception:
            self.log("Couldn't decode message!")
            return

        if decoded['component'] == 'isomer.auth' and decoded['action'] == 'fail':
            self.log("Login failed. Check credentials and url!", lvl=error)
            sys.exit()

    @handler("read", channel="stdin")
    def stdin_read(self, data):
        """read Event (on channel ``stdin``)
        This is the event handler for ``read`` events specifically from the
        ``stdin`` channel. This is triggered each time stdin has data that
        it has read.
        """

        data = data.strip().decode("utf-8")
        self.log("Incoming:", data, lvl=verbose)

        if len(data) == 0:
            self.log('Use /help to get a list of client commands')
            return

        if data[0] == "/":
            cmd = data[1:]
            args = []
            if ' ' in cmd:
                cmd, args = cmd.split(' ', maxsplit=1)
                args = args.split(' ')
            if cmd in self.hooks:
                self.log('Firing hooked event:', cmd, args, lvl=debug)
                self.fireEvent(self.hooks[cmd](*args))
            if cmd.lower() in ('send', 's'):
                data = " ".join(args)
                json = loads(" ".join(args))
                self.log("Transmitting:", data, pretty=True, lvl=debug)
                self.fireEvent(write(data), 'ws')
            if cmd.lower() in ('history', 'h'):
                position = int(args[0])
                pretty = '-p' in args
                self.log('Response [%i]: %s' % (position, self.messages[position]),
                         pretty=pretty)
            if cmd.lower() == "test":
                self.fireEvent(get_data('user', {'name': 'riot'}))
            if cmd.lower() in ('quit', 'q'):
                self.log('Initiating system exit in 3 seconds on request.', lvl=verbose)
                Timer(3, Event.create("quit")).register(self)

    def get_data(self, event: get_data):
        """Request data from Isomer server"""

        request = {
            'component': 'isomer.events.objectmanager',
            'action': 'search',
            'data': {
                'schema': event.schema,
                'search': event.search_filter,
                'req': self._request_id
            }
        }

        self._transmit(request)
        self._request_id += 1
