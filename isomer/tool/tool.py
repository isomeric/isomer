from isomer.tool.create_module import create_module
from isomer.tool.configuration import config
from isomer.tool.backup import db_export, db_import
from isomer.tool.database import db
from isomer.tool.objects import objects
from isomer.tool.installer import install, uninstall
from isomer.tool.instance import instance
from isomer.tool.environment import environment
from isomer.tool.system import system
from isomer.tool.rbac import rbac
from isomer.tool.remote import remote
from isomer.tool.user import user
from isomer.tool.misc import cmdmap, shell
from isomer.tool.cli import cli
from isomer.launcher import launch

cli.add_command(create_module)
cli.add_command(instance)
cli.add_command(environment)
cli.add_command(system)
cli.add_command(config)
cli.add_command(install)
cli.add_command(uninstall)
cli.add_command(cmdmap)
cli.add_command(shell)
cli.add_command(remote)

db.add_command(user)
db.add_command(rbac)
db.add_command(objects)
db.add_command(db_export)
db.add_command(db_import)

cli.add_command(db)

cli.add_command(launch)

isotool = cli
