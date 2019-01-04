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

from typing import Dict, List

from collections import OrderedDict
from functools import wraps
import os
import shutil
import json
import copy
import glob


# Known migrations
_registered_migrations = OrderedDict()


def _perform_migrations(from_version: int, to_version: int, data: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Run required migrations on the given a dict, where the keys of the dict are the schema names,
    and under each is the data from that schema

    :param from_version: the initial schema version of the data
    :param to_version: the schema version to finish at
    :param data: a dict containing the data to migrate
    :return: a dict containing the upgraded data
    """
    # Deep copy the data as migration should be a pure function
    data = copy.deepcopy(data)
    for i in range(from_version + 1, to_version + 1):
        data = _registered_migrations[i](data)
    return data


def _perform_backups(schema_version: int, datastore_paths: List[str]) -> None:
    for datastore in datastore_paths:
        backup_path = os.path.join(os.path.dirname(datastore), 'backups')
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        filename = os.path.splitext(os.path.basename(datastore))[0]
        new_file_path = os.path.join(backup_path, '%s.backup.%d.json' % (filename, schema_version))
        shutil.copyfile(datastore, new_file_path)


def _load_schema_version(data_root: str) -> int:
    if not os.path.exists(os.path.join(data_root, 'metadata.json')):
        return 0
    with open(os.path.join(data_root, 'metadata.json'), 'rt') as f:
        metadata: Dict = json.load(f)
        return metadata.get('schema_version', 0)


def _save_schema_version(data_root: str, schema_version: int) -> None:
    metadata = dict()
    if os.path.exists(os.path.join(data_root, 'metadata.json')):
        with open(os.path.join(data_root, 'metadata.json'), 'rt') as f:
            metadata = json.load(f)
    metadata['schema_version'] = schema_version
    with open(os.path.join(data_root, 'metadata.json'), 'wt') as f:
        json.dump(metadata, f, indent=4, sort_keys=True)


def _get_players_to_migrate(data_root: str) -> List[str]:
    """
    Get the list of players currently registered

    :param data_root: the root of the data store directory
    :return: the list of registered player login names
    """
    if not os.path.exists(os.path.join(data_root, 'accountdatabase.json')):
        # No account database
        return []
    with open(os.path.join(data_root, 'accountdatabase.json'), 'rt') as f:
        accounts = json.load(f)
    return [acc['login_name'] for acc in accounts if 'login_name' in acc]


def _get_datastores_for_player(data_root: str, player_name: str) -> List[str]:
    return glob.glob(os.path.join(data_root, 'players', '%s_*.json' % player_name), recursive=True)


def _load_datastores(data_root: str, player_name: str) -> Dict[str, Dict]:
    # Find datastores for the player
    player_datastores = _get_datastores_for_player(data_root, player_name)
    result = OrderedDict()
    # Load each of them under the top-level dict
    for ds in player_datastores:
        datastore_name: str = os.path.splitext(os.path.basename(ds))[0].split('_')[-1]
        with open(ds, 'rt') as f:
            result[datastore_name] = json.load(f)
    return result


def _save_datastores(data_root: str, player_name: str, player_data: Dict[str, Dict]) -> None:
    for ds_name, ds_data in player_data.items():
        file_path = os.path.join(data_root, 'players', '%s_%s.json' % (player_name, ds_name))
        with open(file_path, 'wt') as f:
            json.dump(ds_data, f, indent=4, sort_keys=True)


# Migrates all files of all schemas
def run_migrations(data_root_path: str) -> None:
    """
    Run data migrations on all necessary files

    This does no error checking; if any migration fails a ValueError will be raised at that point

    :param data_root_path: the root path of data files to migrate
    :return: None
    """
    existing_version = _load_schema_version(data_root_path)

    # Determine the highest available migration
    upgraded_version = existing_version
    while upgraded_version + 1 in _registered_migrations:
        upgraded_version += 1

    # Exit early if no migration is needed
    if upgraded_version == existing_version:
        return

    # Migrate each player's datastores in turn
    for player in _get_players_to_migrate(data_root_path):
        # Back up
        datastores_to_migrate = _get_datastores_for_player(data_root_path, player)
        _perform_backups(existing_version, datastores_to_migrate)

        # Load current data, and delete the on-disk copy in case we rename/remove a datastore in migration
        current_datastores = _load_datastores(data_root_path, player)
        for ds in datastores_to_migrate:
            os.remove(ds)

        # Run migrations and save
        upgraded_datatores = _perform_migrations(existing_version, upgraded_version, current_datastores)
        _save_datastores(data_root_path, player, upgraded_datatores)

    # Write the new schema version
    _save_schema_version(data_root_path, upgraded_version)


# Migration decorator
def taserver_migration(schema_version: int):
    """
    Decorator denoting a TAServer schema migration
    Should decorate a function taking one argument, being a dict to be upgraded, and returning the upgraded dict

    Migrations should raise a ValueError if the data they attempt to upgrade is invalid

    :param schema_version: the version of the schema this migration upgrades to
                           there should only be one migration for a given version of a given schema
                           and there must be a contiguous range of migrations available, starting at version 1
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(data: Dict):
            return func(data)
        # Register the migration
        _registered_migrations[schema_version] = func
        return wrapped_func
    return decorator
