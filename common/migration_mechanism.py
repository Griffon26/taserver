#!/usr/bin/env python3
#
# Copyright (C) 2018  Joseph Spearritt <mcoot@tamods.org>
#
# This file is part of taserver
#
# taserver is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# taserver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with taserver.  If not, see <http://www.gnu.org/licenses/>.
#

from typing import Dict

from collections import OrderedDict
from functools import wraps
import os
import json
import copy
import glob


_SCHEMA_VERSION_KEY = 'schema_version'

# Known migrations
_registered_migrations = OrderedDict()


def _does_file_match_schema(schema_name: str, file_path: str) -> bool:
    filename: str = os.path.splitext(os.path.basename(file_path))[0]
    if filename == schema_name:
        # <schema_name>.json case
        return True
    if len(filename.split('_')) > 0 and filename.split('_')[-1] == schema_name:
        # <player_name>_<schema_name>.json case
        return True
    return False


def _needs_migration(schema_name: str, data: Dict) -> bool:
    schema_version = data.get(_SCHEMA_VERSION_KEY, 0)
    return schema_version + 1 in _registered_migrations.get(schema_name, OrderedDict())


def _perform_migrations(schema_name: str, data: Dict) -> Dict:
    """
    Run required migrations on the given a dict of json, representing data of the given schema

    :param schema_name: the schema name for this data
    :param data: a dict containing the data to migrate
    :return: a dict containing the upgraded data
    """
    # Deep copy the data, migration should be a pure function
    data = copy.deepcopy(data)
    # Determine the version of the data (0 if none available)
    schema_version = data.get(_SCHEMA_VERSION_KEY, 0)
    current_version = schema_version + 1
    while _needs_migration(schema_name, data):
        # Run the current migration
        # First remove the version key, the migration code shouldn't touch it
        if _SCHEMA_VERSION_KEY in data:
            del data[_SCHEMA_VERSION_KEY]
        data = _registered_migrations[schema_name][current_version](data)
        data[_SCHEMA_VERSION_KEY] = current_version
        current_version += 1
    # No migration to the next version up, so stop migrating
    return data


# Migrates all files of all schemas
def run_migrations(data_root_path: str) -> None:
    """
    Run data migrations on all necessary files

    This does no error checking; if any migration fails a ValueError will be raised at that point

    :param data_root_path: the root path of data files to migrate
    :return: None
    """
    all_json_files = glob.glob('%s/**/*.json' % data_root_path, recursive=True)
    # Migrate each known schema in turn
    # Using OrderedDict so this will be consistent in ordering
    for schema_name, available_migrations in _registered_migrations.items():
        # Upgrade any json files that match this schema
        for file_path in all_json_files:
            if _does_file_match_schema(schema_name, file_path):
                with open(file_path, 'rt') as f:
                    data = json.load(f)
                # Don't do migrations for this file if we know we're at the current version
                if not _needs_migration(schema_name, data):
                    break
                # Create a backup for the data
                filename = os.path.splitext(os.path.basename(file_path))[0]
                filedir = os.path.dirname(file_path)
                with open(os.path.join(filedir, '%s.bkp.json' % filename), 'wt') as f:
                    json.dump(data, f, indent=4, sort_keys=True)
                # Perform needed migrations on this data
                upgraded_data = _perform_migrations(schema_name, data)
                # Overwrite the data
                with open(file_path, 'wt') as f:
                    json.dump(upgraded_data, f, indent=4, sort_keys=True)


# Migration decorator
def taserver_migration(schema_name: str, schema_version: int):
    """
    Decorator denoting a TAServer schema migration
    Should decorate a function taking one argument, being a dict to be upgraded, and returning the upgraded dict

    Migrations should raise a ValueError if the data they attempt to upgrade is invalid

    :param schema_name: the name of the schema to be upgraded, e.g. 'friends', 'loadouts'
                        data files must be named in one of two formats:
                            - <player_name>_<schema_name>.json
                            - <schema_name>.json
    :param schema_version: the version of the schema this migration upgrades to
                           there should only be one migration for a given version of a given schema
                           and there must be a contiguous range of migrations available, starting at version 1
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(data: Dict):
            return func(data)

        # Register the migration
        if schema_name not in _registered_migrations:
            _registered_migrations[schema_name] = OrderedDict()
        _registered_migrations[schema_name][schema_version] = func

        return wrapped_func
    return decorator
