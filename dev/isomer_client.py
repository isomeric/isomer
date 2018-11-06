
import click
import sys

from isomer.component import LoggingComponent
from isomer.logger import debug, verbose
from circuits import handler, Manager, Debugger
from circuits.io import stdin
from circuits.net.events import write
from circuits.web.websockets.client import WebSocketClient
from json import dumps, loads

from dev.tools import ask


class HFOSClient(LoggingComponent):
    def __init__(self, *args, **kwargs):
        super(HFOSClient, self).__init__(*args, **kwargs)
        self.url = '{protocol}://{host}:{port}/websocket'.format(**kwargs)
        self.client = WebSocketClient(self.url).register(self)
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')

        self.max_length = 100

        self.messages = []
        self.hooks = {}

        stdin.register(self)

    @handler("registered", channel='ws')
    def connected(self, event, *args):
        if 'ws' not in event.channels:
            return
        self.log('Transmitting login')

        packet = {
            'component': 'auth',
            'action': 'login',
            'data': {
                'username': self.username,
                'password': self.password
            }
        }

        self.fireEvent(write(dumps(packet)), 'ws')

    @handler("read", channel='ws')
    def read(self, *args):
        msg = args[0]
        self.messages.append(msg)
        if len(msg) > self.max_length:
            msg = msg[:self.max_length] + " ..."
        self.log("Response [%i]: %s" % (len(self.messages), msg))

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
                self.log('Response [%i]: %s' % (position, self.messages[position]), pretty=pretty)
            if cmd.lower() in ('quit', 'q'):
                self.log('Quitting on request.', lvl=verbose)
                sys.exit()


@click.command()
@click.option("--protocol", help="Define protocol for server (ws/wss)",
              type=str, default='wss')
@click.option("--port", help="Define port for server", type=int,
              default=443)
@click.option("--host", help="Define hostname for server", type=str,
              default='0.0.0.0')
@click.option("-u", "--username", help="Specify username", type=str,
              default='anonymous')
@click.option("-p", "--password", help="Specify password", type=str,
              default='')
@click.option("--debug", help="Start debugger", is_flag=True,
              default=False)
def main(**kwargs):
    user = kwargs.get('username')
    if user != 'anonymous' and kwargs.get('password') == '':
        kwargs['password'] = ask('Enter password for ' + user + ':',
                                 password=True)

    manager = Manager()
    if kwargs.get('debug'):
        debugger = Debugger().register(manager)
    client = HFOSClient(**kwargs).register(manager)

    manager.run()


if __name__ == '__main__':
    main()
