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
Miscellaneous utility functions for Isomer
"""

import gettext
import json
import os
import copy
import re

from isomer.logger import isolog, verbose, warn

localedir = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "locale")
)


def l10n_log(*args, **kwargs):
    """Log as L10N emitter"""

    kwargs.update({"emitter": "L10N", "frame_ref": 2})
    isolog(*args, **kwargs)


def all_languages():
    """Compile a list of all available language translations"""

    rv = []

    for lang in os.listdir(localedir):
        base = str(lang).split("_")[0].split(".")[0].split("@")[0]
        if 2 <= len(base) <= 3 and all(c.islower() for c in base):
            if base != "all":
                rv.append(lang)
    rv.sort()
    rv.append("en")
    l10n_log("Registered languages:", rv, lvl=verbose)

    return rv


def language_token_to_name(languages):
    """Get a descriptive title for all languages"""

    result = {}

    with open(os.path.join(localedir, "languages.json"), "r") as f:
        language_lookup = json.load(f)

    for language in languages:
        language = language.lower()
        try:
            result[language] = language_lookup[language]
        except KeyError:
            l10n_log("Language token lookup not found:", language, lvl=warn)
            result[language] = language

    return result


class Domain:
    """Gettext domain capable of translating into all registered languages"""

    def __init__(self, domain):
        self._domain = domain
        self._translations = {}

    def _get_translation(self, lang):
        """Add a new translation language to the live gettext translator"""

        try:
            return self._translations[lang]
        except KeyError:
            # The fact that `fallback=True` is not the default is a serious design flaw.
            rv = self._translations[lang] = gettext.translation(
                self._domain, localedir=localedir, languages=[lang], fallback=True
            )
            return rv

    def get(self, lang, msg):
        """Return a message translated to a specified language"""

        return self._get_translation(lang).gettext(msg)


def print_messages(domain, msg):
    """Debugging function to print all message language variants"""

    domain = Domain(domain)
    for lang in all_languages():
        l10n_log(lang, ":", domain.get(lang, msg))


def i18n(msg, event=None, lang="en", domain="backend"):
    """Gettext function wrapper to return a message in a specified language by
    domain

    To use internationalization (i18n) on your messages, import it as '_' and
    use as usual. Do not forget to supply the client's language setting."""

    if event is not None:
        language = event.client.language
    else:
        language = lang

    domain = Domain(domain)
    return domain.get(language, msg)


def nested_map_find(d, keys):
    """Looks up a nested dictionary by traversing a list of keys"""

    if isinstance(keys, str):
        keys = keys.split(".")
    rv = d
    for key in keys:
        rv = rv[key]
    return rv


def nested_map_update(d, u, *keys):
    """Modifies a nested dictionary by traversing a list of keys"""
    d = copy.deepcopy(d)
    keys = keys[0]
    if len(keys) > 1:
        d[keys[0]] = nested_map_update(d[keys[0]], u, keys[1:])
    else:
        if u is not None:
            d[keys[0]] = u
        else:
            del d[keys[0]]
    return d


# TODO: Somehow these two fail the tests, although they seem to work fine
#   in non-test situations.

# def nested_map_find(data_dict, map_list):
#     """Looks up a nested dictionary by traversing a list of keys
#
#     :param dict data_dict: Nested dictionary to traverse
#     :param list map_list: List of keys to traverse along
#     :return object: The resulting value or None if not found
#     """
#
#     return reduce(operator.getitem, map_list, data_dict)
#
#
# def nested_map_update(data_dict, value, map_list):
#     """Modifies a nested dictionary by traversing a list of keys
#
#     :param dict data_dict: Nested dictionary to traverse
#     :param object value: New value to set at found key
#     :param list map_list: List of keys to traverse along
#     :return object: The resulting value or None if not found
#     """
#
#     nested_map_find(data_dict, map_list[:-1])[map_list[-1]] = value


def sorted_alphanumerical(l, reverse=False):
    """ Sort the given iterable in the way that humans expect."""

    # From: http://stackoverflow.com/questions/2669059/ddg#2669120

    converted = lambda text: int(text) if text.isdigit() else text
    alphanumerical_key = lambda key: [converted(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanumerical_key, reverse=reverse)


logo = """
                   .'::'.
                .':cccccc:'.
             .':cccccccccccc:'.
          .':ccccccc;..;ccccccc:'.
       .':ccccccc;.      .;ccccccc:'.
    .':ccccccc;.            .;ccccccc:'.
   ;cccccccc:.                .:cccccccc;
     .:ccccccc;.            .;ccccccc:'
        .:ccccccc;.      .;ccccccc:.
           .:ccccccc;..;ccccccc:.
              .;cccccccccccc:.
                 .;cccccc:.
                    .;;.
                                             """
