import click
from circuits import Manager, Debugger

from isomer.client import IsomerClient
from isomer.logger import isolog, set_color
from isomer.tool import ask_password


def log(*args, **kwargs):
    """Log as emitter 'ISOCLIENT'"""
    isolog(*args, **kwargs, emitter="ISOCLIENT")


@click.command()
@click.option("--protocol", help="Define protocol for server (ws/wss)",
              type=str, default='wss')
@click.option("--port", "-p", help="Define port for server", type=int,
              default=443)
@click.option("--host", "-h", help="Define hostname for server", type=str,
              default='0.0.0.0')
@click.option("-u", "--username", help="Specify username", type=str,
              default='anonymous')
@click.option("-p", "--password", help="Specify password", type=str,
              default='')
@click.option("--url", help="Specify alternate url", default="websocket", type=str)
@click.option("--debug", help="Start debugger", is_flag=True,
              default=False)
def main(**kwargs):
    """Client CLI utility"""

    set_color()

    user = kwargs.get('username')
    if user != 'anonymous' and kwargs.get('password') == '':
        kwargs['password'] = ask_password()

    log(kwargs, pretty=True)

    manager = Manager()
    if kwargs.get('debug'):
        debugger = Debugger().register(manager)
    client = IsomerClient(**kwargs).register(manager)

    manager.run()


if __name__ == '__main__':
    main()
