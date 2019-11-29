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

"""

Provisioning: Basic Functionality
=================================

Contains
--------

Basic functionality around provisioning.


"""

import networkx
from jsonschema import ValidationError

from isomer.logger import isolog, debug, verbose, warn, error


def log(*args, **kwargs):
    """Log as Emitter:MANAGE"""

    kwargs.update({"emitter": "PROVISIONS", "frame_ref": 2})
    isolog(*args, **kwargs)


def provisionList(
    items, database_name, overwrite=False, clear=False, skip_user_check=False
):
    """Provisions a list of items according to their schema

    :param items: A list of provisionable items.
    :param database_name:
    :param overwrite: Causes existing items to be overwritten
    :param clear: Clears the collection first (Danger!)
    :param skip_user_check: Skips checking if a system user is existing already (for user provisioning)
    :return:
    """

    log("Provisioning", items, database_name, lvl=debug)

    def get_system_user():
        """Retrieves the node local system user"""

        user = objectmodels["user"].find_one({"name": "System"})

        try:
            log("System user uuid: ", user.uuid, lvl=verbose)
            return user.uuid
        except AttributeError as system_user_error:
            log("No system user found:", system_user_error, lvl=warn)
            log(
                "Please install the user provision to setup a system user or "
                "check your database configuration",
                lvl=error,
            )
            return False

    # TODO: Do not check this on specific objects but on the model (i.e. once)
    def needs_owner(obj):
        """Determines whether a basic object has an ownership field"""
        for privilege in obj._fields.get("perms", None):
            if "owner" in obj._fields["perms"][privilege]:
                return True

        return False

    import pymongo
    from isomer.database import objectmodels, dbhost, dbport, dbname

    database_object = objectmodels[database_name]

    log(dbhost, dbname)
    # TODO: Fix this to make use of the dbhost

    client = pymongo.MongoClient(dbhost, dbport)
    db = client[dbname]

    if not skip_user_check:
        system_user = get_system_user()

        if not system_user:
            return
    else:
        # TODO: Evaluate what to do instead of using a hardcoded UUID
        # This is usually only here for provisioning the system user
        # One way to avoid this, is to create (instead of provision)
        # this one upon system installation.
        system_user = "0ba87daa-d315-462e-9f2e-6091d768fd36"

    col_name = database_object.collection_name()

    if clear is True:
        log("Clearing collection for", col_name, lvl=warn)
        db.drop_collection(col_name)
    counter = 0

    for no, item in enumerate(items):
        new_object = None
        item_uuid = item["uuid"]
        log("Validating object (%i/%i):" % (no + 1, len(items)), item_uuid, lvl=debug)

        if database_object.count({"uuid": item_uuid}) > 0:
            log("Object already present", lvl=warn)
            if overwrite is False:
                log("Not updating item", item, lvl=warn)
            else:
                log("Overwriting item: ", item_uuid, lvl=warn)
                new_object = database_object.find_one({"uuid": item_uuid})
                new_object._fields.update(item)
        else:
            new_object = database_object(item)

        if new_object is not None:
            try:
                if needs_owner(new_object):
                    if not hasattr(new_object, "owner"):
                        log("Adding system owner to object.", lvl=verbose)
                        new_object.owner = system_user
            except Exception as e:
                log("Error during ownership test:", e, type(e), exc=True, lvl=error)
            try:
                new_object.validate()
                new_object.save()
                counter += 1
            except ValidationError as e:
                raise ValidationError(
                    "Could not provision object: " + str(item_uuid), e
                )

    log("Provisioned %i out of %i items successfully." % (counter, len(items)))


def provision(list_provisions=False, overwrite=False, clear_provisions=False,
              package=None, installed=None):
    from isomer.provisions import build_provision_store
    from isomer.database import objectmodels

    provision_store = build_provision_store()

    if installed is None:
        installed = []

    def sort_dependencies(items):
        """Topologically sort the dependency tree"""

        g = networkx.DiGraph()
        log("Sorting dependencies")

        for key, item in items:
            log("key: ", key, "item:", item, pretty=True, lvl=debug)
            dependencies = item.get("dependencies", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]

            if key not in g:
                g.add_node(key)

            for link in dependencies:
                g.add_edge(key, link)

        if not networkx.is_directed_acyclic_graph(g):
            log("Cycles in provisioning dependency graph detected!", lvl=error)
            log("Involved provisions:", list(networkx.simple_cycles(g)), lvl=error)

        topology = list(networkx.algorithms.topological_sort(g))
        topology.reverse()
        topology = list(set(topology).difference(installed))

        # log(topology, pretty=True)

        return topology

    sorted_provisions = sort_dependencies(provision_store.items())

    # These need to be installed first in that order:
    if 'system' in sorted_provisions:
        sorted_provisions.remove('system')
    if 'user' in sorted_provisions:
        sorted_provisions.remove('user')
    if 'system' not in installed:
        sorted_provisions.insert(0, 'system')
    if 'user' not in installed:
        sorted_provisions.insert(0, 'user')

    if list_provisions:
        log(sorted_provisions, pretty=True)
        exit()

    def provision_item(provision_name):
        """Provision a single provisioning element"""

        item = provision_store[provision_name]

        method = item.get("method", provisionList)
        model = item.get("model")
        data = item.get("data")

        method(data, model, overwrite=overwrite, clear=clear_provisions)

        confirm_provision(provision_name)

    def confirm_provision(provision_name):
        if provision_name == 'user':
            log('Not confirming system user provision')
            return
        systemconfig = objectmodels['systemconfig'].find_one({'active': True})
        if provision_name not in systemconfig.provisions['packages']:
            systemconfig.provisions['packages'].append(provision_name)
            systemconfig.save()

    if package is not None:
        if package in provision_store:
            log("Provisioning ", package, pretty=True)
            provision_item(package)
        else:
            log(
                "Unknown package: ",
                package,
                "\nValid provisionable packages are",
                list(provision_store.keys()),
                lvl=error,
                emitter="MANAGE",
            )
    else:
        for name in sorted_provisions:
            log("Provisioning", name, pretty=True)
            provision_item(name)
