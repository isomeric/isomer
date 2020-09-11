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

from isomer.logger import isolog, warn  # , verbose
from isomer.misc.std import colors
from pycountry import countries, subdivisions  # , currencies, languages,
from random import randint, choice

"""


Module defaultform
==================

A default form listing all object elements with submit button.


"""

savebutton = {
    "type": "button",
    "title": "Save Object",
    "condition": "$ctrl.readonly === false",
    "onClick": "$ctrl.submitObject()",
}

createnewbutton = {
    "type": "button",
    "title": "Save & Create new",
    "condition": "$ctrl.readonly === false",
    "onClick": "$ctrl.save_createObject()",
}

deletebutton = {
    "type": "button",
    "title": "Delete Object",
    "condition": "$ctrl.readonly === false",
    "onClick": "$ctrl.deleteObject()",
}

editbuttons = {
    "type": "actions",
    "condition": "$ctrl.readonly === false",
    "items": [savebutton, createnewbutton, deletebutton],
}

defaultform = ["*", editbuttons]

changeonlyform = [
    "*",
    {"type": "actions", "condition": "$ctrl.readonly === false", "items": [savebutton]},
]

readonlyform = ["*"]

noform = []


def lookup_field(
    key,
    lookup_type=None,
    placeholder=None,
    html_class="div",
    select_type="strapselect",
    mapping="uuid",
    search_filter=None,
):
    """Generates a lookup field for form definitions"""

    if lookup_type is None:
        lookup_type = key

    if placeholder is None:
        placeholder = "Select a " + lookup_type

    result = {
        "key": key,
        "htmlClass": html_class,
        "type": select_type,
        "placeholder": placeholder,
        "options": {
            "type": lookup_type,
            "asyncCallback": "$ctrl.getFormData",
            "map": {"valueProperty": mapping, "nameProperty": "name"},
        },
    }

    if search_filter is not None:
        result["options"]["search_filter"] = search_filter

    return result


def lookup_field_multiple(
    key,
    subkey=None,
    button="Add",
    lookup_type=None,
    placeholder=None,
    html_class="div",
    select_type="strapselect",
    mapping="uuid",
):
    if subkey is None:
        subkey = key + "[]"

    return {
        "key": key,
        "add": button,
        "htmlClass": html_class,
        "startEmpty": True,
        "style": {"add": "btn-success"},
        "items": [
            {
                "key": subkey,
                "type": select_type,
                "placeholder": placeholder,
                "options": {
                    "type": lookup_type,
                    "asyncCallback": "$ctrl.getFormData",
                    "map": {"valueProperty": mapping, "nameProperty": "name"},
                },
            }
        ],
    }


def lookup_object(key, lookup_type=None, actions=None):
    """Returns a lookup button to inspect a selected object"""

    if lookup_type is None:
        lookup_type = key

    if actions is None:
        actions = ["edit", "create"]

    template = ""

    for action in actions:
        uuid_key = "{{model.%s}}" % key
        condition = 'ng-show="model.%s != null"' % key

        if action == "edit":
            icon = "pencil"
            button_class = "success"
        elif action == "view":
            icon = "search"
            button_class = "info"
        elif action == "create":
            icon = "plus"
            condition = ""
            button_class = "info"
            uuid_key = ""
        elif action == "unset":
            # TODO: This needs to change the link to unset the model attribute
            icon = "plus"
            condition = ""
            button_class = "info"
        elif action == "delete":
            icon = "trash"
            button_class = "danger"
        else:
            icon = "question"
            condition = ""
            button_class = "info"

        template += (
            '<a %s class="btn btn-%s btn-sm"'
            'href="/#!/editor/%s/%s/%s">'
            '<span class="fa fa-%s"></span>'
            "</a>" % (condition, button_class, lookup_type, uuid_key, action, icon)
        )

    result = {"key": "lookup_" + key, "type": "template", "template": template}

    return result


def create_object(key, lookup_type):
    """Returns a lookup button to inspect a selected object"""

    result = {
        "key": "create_" + key,
        "type": "template",
        "template": '<a href="/#!/editor/' + lookup_type + '//create">Create new</a>',
    }

    return result


def fieldset(title, items, options=None):
    """A field set with a title and sub items"""
    result = {"title": title, "type": "fieldset", "items": items}
    if options is not None:
        result.update(options)

    return result


def section(rows: int, columns: int, items: list,
            label: str = None, condition: str = None):
    """A section consisting of rows and columns

    :param rows: Number of rows
    :param columns: Number of columns
    :param items: Section items
    :param label: Optional label - if you use this, unpack the section with
            ``*section(.., label="foo")`` in your form
    :param condition: A angular-schema-form model condition
    :return: A complex form section object
    """

    if label is None:
        label = "Section " + choice(colors) + " " + str(randint(0, 500))
        label_widget = None
    else:
        label_widget = {'type': 'help', 'helpvalue': '<h2>' + label + '</h2>'}

    sections = []

    column_class = "section-column col-sm-%i" % (12 / columns)

    items_total = 0
    items_count = 0
    for row in items:
        items_total += len(row)

    for vertical in range(columns):
        column_items = []
        for horizontal in range(rows):
            try:
                item = items[horizontal][vertical]
                column_items.append(item)
                items_count += 1
            except IndexError:
                # No item in this part of the form, doesn't matter
                pass
        column = {"type": "section", "htmlClass": column_class, "items": column_items}
        sections.append(column)

    if items_count < items_total:
        isolog(
            items_total - items_count,
            "field(s) in",
            label,
            "omitted, due to missing row/column:",
            lvl=warn,
            emitter="FORMS",
            tb=True,
            frame=2,
        )

    result = {"type": "section", "htmlClass": "row", "items": sections}

    if condition is not None:
        result["condition"] = condition

    if label_widget is not None:
        result = [label_widget, result]

    return result


def emptyArray(key, add_label=None):
    """An array that starts empty"""

    result = {"key": key, "startEmpty": True}
    if add_label is not None:
        result["add"] = add_label
        result["style"] = {"add": "btn-success"}
    return result


def tabset(titles, contents):
    """A tabbed container widget"""

    tabs = []
    for no, title in enumerate(titles):
        tab = {"title": title}
        content = contents[no]
        if isinstance(content, list):
            tab["items"] = content
        else:
            tab["items"] = [content]
        tabs.append(tab)

    result = {"type": "tabs", "tabs": tabs}

    return result


def rating_widget(key="rating", maximum=10):
    """A customizable star rating widget"""
    widget = {
        "key": "rating",
        "type": "template",
        "template": '<div class="rating">'
        '   <span class="fa fa-star-o" ng-repeat="rating in []|range: {1} - model.{0}"'
        '         ng-click="model.{0} = {1} - rating"></span>'
        '   <span class="fa fa-star" ng-repeat="rating in []|range: model.{0}"'
        '         ng-click="model.{0} = model.{0} - rating"></span>'
        "</div>"
        "<span>{{model.{0}}} out of 10</span>".format(key, maximum),
    }

    return widget


# def collapsible(key, elements, label=None):
#     """Widget for a collapsible section"""
#
#     if not label:
#         label = key
#
#     result = {
#         "type": "template",
#         "template": '<h3 ng-click="form.'
#         + key
#         + "_collapsed = !form."
#         + key
#         + '_collapsed">'
#         + label
#         + "<span ng-class=\"{'fa-chevron-up': form."
#         + key
#         + "_collapsed,"
#         "                 'fa-chevron-down': !form." + key + '_collapsed}" class="fa">'
#         "</span>"
#         "</h3>",
#     }
#
#     return (
#         result,
#         {
#             "type": "section",
#             "condition": "form." + key + "_collapsed",
#             "items": elements,
#         },
#     )
#

def event_button(key, title, target, action, data=None):
    """Template for an event emitting button"""
    if data is None:
        data = "model"

    widget = {
        "key": key,
        "type": "button",
        "onClick": '$ctrl.formAction("%s", "%s", "%s")' % (target, action, data),
        "title": title,
    }

    return widget


def country_field(key="country"):
    """Provides a select box for country selection"""

    country_list = list(countries)
    title_map = []
    for item in country_list:
        title_map.append({"value": item.alpha_3, "name": item.name})

    widget = {"key": key, "type": "uiselect", "titleMap": title_map}

    return widget


def area_field(key="area"):
    """Provides a select box for country selection"""

    area_list = list(subdivisions)
    title_map = []
    for item in area_list:
        title_map.append({"value": item.code, "name": item.name})

    widget = {"key": key, "type": "uiselect", "titleMap": title_map}

    return widget


def horizontal_divider():
    """Inserts a horizontal ruler/divider"""

    widget = {"type": "help", "helpvalue": "<hr />"}
    return widget


def test():
    """Development function to manually test all widgets"""
    # TODO: Get rid of this and put it into testing
    print("Hello")
    from pprint import pprint

    section_thing = section(2, 3, [["first", "second", "third"], ["fourth", "fifth"]])

    pprint(section_thing)

    fieldset_thing = fieldset("Fieldset", ["1", "2", "3"])

    pprint(fieldset_thing)

    thing = tabset(["First", "Second"], [section_thing, fieldset_thing])

    pprint(thing)


if __name__ == "__main__":
    test()
