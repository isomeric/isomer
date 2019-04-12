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

Module: OM
==========

OM manager


"""

from uuid import uuid4

from isomer.component import handler
from isomer.database import objectmodels, ValidationError
from isomer.schemastore import schemastore
from isomer.events.client import send
from isomer.events.objectmanager import get, search, getlist, change, put, objectcreation, objectchange, delete, \
    objectdeletion
from isomer.logger import warn, verbose, error, debug, critical
from pymongo import ASCENDING, DESCENDING
from isomer.ui.objectmanager.basemanager import ObjectBaseManager, WARNSIZE


class CrudOperations(ObjectBaseManager):

    @handler(get)
    def get(self, event):
        """Get a specified object"""

        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        object_filter = self._get_filter(event)

        if 'subscribe' in data:
            do_subscribe = data['subscribe'] is True
        else:
            do_subscribe = False

        try:
            uuid = str(data['uuid'])
        except (KeyError, TypeError):
            uuid = ""

        opts = schemastore[schema].get('options', {})
        hidden = opts.get('hidden', [])

        if object_filter == {}:
            if uuid == "":
                self.log('Object with no filter/uuid requested:', schema,
                         data,
                         lvl=warn)
                return
            object_filter = {'uuid': uuid}

        storage_object = None
        storage_object = objectmodels[schema].find_one(object_filter)

        if not storage_object:
            self._cancel_by_error(event, uuid + '(' + str(object_filter) + ') of ' + schema +
                                  ' unavailable')
            return

        if storage_object:
            self.log("Object found, checking permissions: ", data, lvl=verbose)

            if not self._check_permissions(user, 'read',
                                           storage_object):
                self._cancel_by_permission(schema, data, event)
                return

            for field in hidden:
                storage_object._fields.pop(field, None)

            if do_subscribe and uuid != "":
                self._add_subscription(uuid, event)

            result = {
                'component': 'isomer.events.objectmanager',
                'action': 'get',
                'data': {
                    'schema': schema,
                    'uuid': uuid,
                    'object': storage_object.serializablefields()
                }
            }
            self._respond(None, result, event)

    @handler(search)
    def search(self, event):
        """Search for an object"""

        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        def get_filter(filter_request):
            # result['$text'] = {'$search': str(data['search'])}
            if filter_request.get('fulltext', False) is True:
                result = {
                    'name': {
                        '$regex': str(filter_request['search']),
                        '$options': '$i'
                    }
                }
            else:
                if isinstance(filter_request['search'], dict):
                    result = filter_request['search']
                else:
                    result = {}

            return result

        object_filter = get_filter(data)

        if 'fields' in data:
            fields = data['fields']
        else:
            fields = []

        skip = data.get('skip', 0)
        limit = data.get('limit', 0)
        sort = data.get('sort', None)
        # page = data.get('page', 0)
        # count = data.get('count', 0)
        #
        # if page > 0 and count > 0:
        #     skip = page * count
        #     limit = count

        if 'subscribe' in data:
            self.log('Subscription:', data['subscribe'], lvl=verbose)
            do_subscribe = data['subscribe'] is True
        else:
            do_subscribe = False

        object_list = []

        size = objectmodels[schema].count(object_filter)

        if size > WARNSIZE and (limit > 0 and limit > WARNSIZE):
            self.log("Getting a very long (", size, ") list of items for ", schema, lvl=warn)

        opts = schemastore[schema].get('options', {})
        hidden = opts.get('hidden', [])

        self.log("result: ", object_filter, ' Schema: ', schema, "Fields: ", fields, lvl=verbose)

        def get_options():
            options = {}

            if skip > 0:
                options['skip'] = skip
            if limit > 0:
                options['limit'] = limit
            if sort is not None:
                options['sort'] = []
                for thing in sort:
                    key = thing[0]
                    direction = thing[1]
                    direction = ASCENDING if direction == 'asc' else DESCENDING
                    options['sort'].append([key, direction])

            return options

        cursor = objectmodels[schema].find(object_filter, **get_options())

        for item in cursor:
            if not self._check_permissions(user, 'list', item):
                continue
            self.log("Search found item: ", item, lvl=verbose)

            try:
                list_item = {'uuid': item.uuid}
                if fields in ('*', ['*']):
                    item_fields = item.serializablefields()
                    for field in hidden:
                        item_fields.pop(field, None)
                    object_list.append(item_fields)
                else:
                    if 'name' in item._fields:
                        list_item['name'] = item.name

                    for field in fields:
                        if field in item._fields and field not in hidden:
                            list_item[field] = item._fields[field]
                        else:
                            list_item[field] = None

                    object_list.append(list_item)

                if do_subscribe:
                    self._add_subscription(item.uuid, event)
            except Exception as e:
                self.log("Faulty object or field: ", e, type(e), item._fields, fields, lvl=error, exc=True)
        # self.log("Generated object search list: ", object_list)

        result = {
            'component': 'isomer.events.objectmanager',
            'action': 'search',
            'data': {
                'schema': schema,
                'list': object_list,
                'size': size
            }
        }

        self._respond(None, result, event)

    @handler(getlist)
    def objectlist(self, event):
        """Get a list of objects"""

        self.log('LEGACY LIST FUNCTION CALLED!', lvl=warn)
        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        object_filter = self._get_filter(event)
        self.log('Object list for', schema, 'requested from',
                 user.account.name, lvl=debug)

        if 'fields' in data:
            fields = data['fields']
        else:
            fields = []

        object_list = []

        opts = schemastore[schema].get('options', {})
        hidden = opts.get('hidden', [])

        if objectmodels[schema].count(object_filter) > WARNSIZE:
            self.log("Getting a very long list of items for ", schema,
                     lvl=warn)

        try:
            for item in objectmodels[schema].find(object_filter):
                try:
                    if not self._check_permissions(user, 'list', item):
                        continue
                    if fields in ('*', ['*']):
                        item_fields = item.serializablefields()
                        for field in hidden:
                            item_fields.pop(field, None)
                        object_list.append(item_fields)
                    else:
                        list_item = {'uuid': item.uuid}

                        if 'name' in item._fields:
                            list_item['name'] = item._fields['name']

                        for field in fields:
                            if field in item._fields and field not in hidden:
                                list_item[field] = item._fields[field]
                            else:
                                list_item[field] = None

                        object_list.append(list_item)
                except Exception as e:
                    self.log("Faulty object or field: ", e, type(e),
                             item._fields, fields, lvl=error, exc=True)
        except ValidationError as e:
            self.log('Invalid object in database encountered!', e, exc=True,
                     lvl=warn)
        # self.log("Generated object list: ", object_list)

        result = {
            'component': 'isomer.events.objectmanager',
            'action': 'getlist',
            'data': {
                'schema': schema,
                'list': object_list
            }
        }

        self._respond(None, result, event)

    @handler(change)
    def change(self, event):
        """Change an existing object"""

        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        try:
            uuid = data['uuid']
            change = data['change']
            field = change['field']
            new_data = change['value']
        except KeyError as e:
            self.log("Update request with missing arguments!", data, e,
                     lvl=critical)
            self._cancel_by_error(event, 'missing_args')
            return

        storage_object = None

        try:
            storage_object = objectmodels[schema].find_one({'uuid': uuid})
        except Exception as e:
            self.log('Change for unknown object requested:', schema, data, lvl=warn)

        if storage_object is None:
            self._cancel_by_error(event, 'not_found')
            return

        if not self._check_permissions(user, 'write', storage_object):
            self._cancel_by_permission(schema, data, event)
            return

        self.log("Changing object:", storage_object._fields, lvl=debug)
        storage_object._fields[field] = new_data

        self.log("Storing object:", storage_object._fields, lvl=debug)
        try:
            storage_object.validate()
        except ValidationError:
            self.log("Validation of changed object failed!",
                     storage_object, lvl=warn)
            self._cancel_by_error(event, 'invalid_object')
            return

        storage_object.save()

        self.log("Object stored.")

        result = {
            'component': 'isomer.events.objectmanager',
            'action': 'change',
            'data': {
                'schema': schema,
                'uuid': uuid
            }
        }

        self._respond(None, result, event)

    @handler(put)
    def put(self, event):
        """Put an object"""

        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        try:
            clientobject = data['obj']
            uuid = clientobject['uuid']
        except KeyError as e:
            self.log("Put request with missing arguments!", e, data,
                     lvl=critical)
            return

        try:
            model = objectmodels[schema]
            created = False
            storage_object = None

            if uuid != 'create':
                storage_object = model.find_one({'uuid': uuid})
            if uuid == 'create' or model.count({'uuid': uuid}) == 0:
                if uuid == 'create':
                    uuid = str(uuid4())
                created = True
                clientobject['uuid'] = uuid
                clientobject['owner'] = user.uuid
                storage_object = model(clientobject)
                if not self._check_create_permission(user, schema):
                    self._cancel_by_permission(schema, data, event)
                    return

            if storage_object is not None:
                if not self._check_permissions(user, 'write', storage_object):
                    self._cancel_by_permission(schema, data, event)
                    return

                self.log("Updating object:", storage_object._fields, lvl=debug)
                storage_object.update(clientobject)

            else:
                storage_object = model(clientobject)
                if not self._check_permissions(user, 'write', storage_object):
                    self._cancel_by_permission(schema, data, event)
                    return

                self.log("Storing object:", storage_object._fields, lvl=debug)
                try:
                    storage_object.validate()
                except ValidationError:
                    self.log("Validation of new object failed!", clientobject,
                             lvl=warn)

            storage_object.save()

            self.log("Object %s stored." % schema)

            # Notify backend listeners

            if created:
                notification = objectcreation(
                    storage_object.uuid, schema, client
                )
            else:
                notification = objectchange(
                    storage_object.uuid, schema, client
                )

            self._update_subscribers(schema, storage_object)

            result = {
                'component': 'isomer.events.objectmanager',
                'action': 'put',
                'data': {
                    'schema': schema,
                    'object': storage_object.serializablefields(),
                    'uuid': storage_object.uuid,
                }
            }

            self._respond(notification, result, event)

        except Exception as e:
            self.log("Error during object storage:", e, type(e), data,
                     lvl=error, exc=True, pretty=True)

    @handler(delete)
    def delete(self, event):
        """Delete an existing object"""

        try:
            data, schema, user, client = self._get_args(event)
        except AttributeError:
            return

        try:
            uuids = data['uuid']

            if not isinstance(uuids, list):
                uuids = [uuids]

            if schema not in objectmodels.keys():
                self.log("Unknown schema encountered: ", schema, lvl=warn)
                return

            for uuid in uuids:
                self.log("Looking for object to be deleted:", uuid, lvl=debug)
                storage_object = objectmodels[schema].find_one({'uuid': uuid})

                if not storage_object:
                    self._cancel_by_error(event, 'not found')
                    return

                self.log("Found object.", lvl=debug)

                if not self._check_permissions(user, 'write', storage_object):
                    self._cancel_by_permission(schema, data, event)
                    return

                # self.log("Fields:", storage_object._fields, "\n\n\n",
                #         storage_object.__dict__)

                storage_object.delete()

                self.log("Deleted. Preparing notification.", lvl=debug)
                notification = objectdeletion(uuid, schema, client)

                if uuid in self.subscriptions:
                    deletion = {
                        'component': 'isomer.events.objectmanager',
                        'action': 'deletion',
                        'data': {
                            'schema': schema,
                            'uuid': uuid,
                        }
                    }
                    for recipient in self.subscriptions[uuid]:
                        self.fireEvent(send(recipient, deletion))

                    del (self.subscriptions[uuid])

                result = {
                    'component': 'isomer.events.objectmanager',
                    'action': 'delete',
                    'data': {
                        'schema': schema,
                        'uuid': storage_object.uuid
                    }
                }

                self._respond(notification, result, event)

        except Exception as e:
            self.log("Error during delete request: ", e, type(e),
                     lvl=error)