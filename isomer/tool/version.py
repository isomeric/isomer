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

Module: Misc
============

Miscellaneous functionality for the management tool.

"""
import json
import os
import click
import git
import requests

from isomer.error import abort
from isomer.logger import error, debug
from isomer.misc import sorted_alphanumerical

from isomer.tool import log, run_process
from isomer.tool.cli import cli
from isomer.tool.defaults import source_api_url, pypi_api_url
from isomer.version import version_info


@cli.command(short_help="Show running isomer tool version")
def version():
    """Log the version information"""

    log("Tool version info:", version_info, os.path.dirname(__file__))


def get_github_releases():
    """Get release data from Github."""

    log("Getting the source api url")
    request = requests.get(source_api_url)

    if not request.ok:
        log("No repository data from github api!", lvl=error)
        return {}

    repo_item = json.loads(request.text or request.content)
    log("Isomer repository: ", repo_item, pretty=True, lvl=debug)
    tags_url = repo_item["tags_url"].split("{")[0]
    log("Releases url:", tags_url, lvl=debug)

    request = requests.get(tags_url)
    if not request.ok:
        log("No tag data from github api!", lvl=error)
        return {}

    release_items = json.loads(request.text or request.content)
    log("Isomer raw releases:", release_items, pretty=True, lvl=debug)
    releases = {}
    for item in release_items:
        releases[item["name"]] = item["tarball_url"]

    return releases


def get_pypi_releases():
    """Get release data from pypi."""

    log("Getting the source api url")
    request = requests.get(pypi_api_url)

    if not request.ok:
        log("No data from pypi api!", lvl=error)
        return {}

    release_items = json.loads(request.text or request.content)
    log("Isomer raw releases:", release_items, pretty=True, lvl=debug)
    releases = {}
    for version_tag, items in release_items["releases"].items():
        if len(items) == 0:
            continue
        for item in items:
            if item["python_version"] != "source":
                continue
            releases[version_tag] = item["url"]

    return releases


def get_git_releases(repository_path, fetch=False):
    """Get release data from a git repository. Optionally, fetch from upstream first"""

    log("Getting git tags from", repository_path)

    releases = {}

    repo = git.Repo(repository_path)

    if fetch is True:
        log("Fetching origin tags")
        success, result = run_process(
            repository_path,
            ["git", "fetch", "--tags", "-v", "origin"],
        )
        if not success:
            log(result, lvl=error)

        #origin = repo.remotes["origin"]
        #log("Origin:", list(origin.urls), pretty=True)
        #origin.fetch(tags=True)

    tags = repo.tags

    log("Raw tags:", tags, pretty=True, lvl=debug)

    for item in tags:
        releases[str(item)] = item

    return releases


@cli.command(short_help="Check software sources for installable Versions")
@click.option(
    "--source", "-s", default=None,
    type=click.Choice(["link", "copy", "git", "github", "pypi"]),
    help="Override instance source (link, copy, git, github)"
)
@click.option("--url", "-u", default="", type=click.Path())
@click.option("--fetch", "-f", default=False, is_flag=True,
              help="Fetch the newest updates on a git repository")
@click.pass_context
def versions(ctx, source, url, fetch):
    """Check instance sources for installable versions"""

    releases = _get_versions(ctx, source, url, fetch)

    releases_keys = sorted_alphanumerical(releases.keys())

    log("Available Isomer releases:", releases_keys, pretty=True)
    log("Latest:", releases_keys[-1])


def _get_versions(ctx, source, url, fetch):

    instance_configuration = ctx.obj["instance_configuration"]

    source = source if source is not None else instance_configuration["source"]

    releases = {}

    if source == "github":
        releases = get_github_releases()
    elif source == "pypi":
        releases = get_pypi_releases()
    elif source == "git":
        if url is not "":
            repo = url
        else:
            repo = instance_configuration["url"]
        releases = get_git_releases(repo, fetch)
    else:
        log("Other methods to acquire versions than github are currently WiP")
        abort(60001)

    return releases
