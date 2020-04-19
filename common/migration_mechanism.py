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
import glob

# Known migrations
_registered_migrations = OrderedDict()


def _perform_backups(data_root: str) -> None:
    backup_num = 0
    backup_path = data_root + ('.%d.bkp' % backup_num)
    while os.path.exists(backup_path):
        backup_num += 1
        backup_path = data_root + ('.%d.bkp' % backup_num)
    shutil.copytree(data_root, backup_path)


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
    return [acc['login_name'] for acc in accounts]


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

    # Back up all datastores
    _perform_backups(data_root_path)

    # Perform each migration in turn
    for i in range(existing_version + 1, upgraded_version + 1):
        _registered_migrations[i](data_root_path)

    # Write the new schema version
    _save_schema_version(data_root_path, upgraded_version)


# Migration decorator
def taserver_migration(schema_version: int):
    """
    Decorator denoting a TAServer schema migration
    Should decorate a function taking the path to the data directory and returning nothing.
    The migration function is essentially a script performing whatever migration required

    Migrations should raise a ValueError if the data they attempt to upgrade is invalid

    :param schema_version: the version of the schema this migration upgrades to
                           there should only be one migration for a given version of a given schema
                           and there must be a contiguous range of migrations available, starting at version 1
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(data_root: str):
            return func(data_root)
        # Register the migration
        _registered_migrations[schema_version] = func
        return wrapped_func
    return decorator


def upgrades_all_players():
    """
    Decorator denoting a function which manipulates player-specific datastores.

    Should decorate a function taking two arguments:
        - a dict of all datastores belonging to one player, with keys being the store name, and values being dicts
        - the player's login name
    and returning a dict of all datastores belonging to that player after the transformation

    The decorator handles loading, saving, and applying the function across all players.

    Will generally be used in conjunction with @taserver_migration in order to allow migrations which are
    transformations of player data

    Contract for a migration function using this decorator:

    1) Function takes the data as a dict where the keys are each existing schemas, under which is data from that schema.
       As a second argument it takes the name of the player currently being migrated
    2) Function returns the data as a dict with keys being the new schemas, under which data is in the new schema format
    3) If the format of the original data is invalid, function raises a ValueError
    4) Function must be referentially transparent, except that it may mutate its argument for convenience
       (but must still return its now-mutated argument), and in that it may raise ValueError if format is invalid
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(data_root: str):
            # Apply this to all known players
            for player in _get_players_to_migrate(data_root):
                datastores_to_migrate = _get_datastores_for_player(data_root, player)
                # Load current data, and delete the on-disk copy in case we rename/remove a datastore in migration
                data = _load_datastores(data_root, player)
                for ds in datastores_to_migrate:
                    os.remove(ds)
                # Perform the function, then save
                upgraded = func(data, player)
                _save_datastores(data_root, player, upgraded)
        return wrapped_func
    return decorator


# Migrations imported at the bottom of the file to work around circular dependency
import common.migrations