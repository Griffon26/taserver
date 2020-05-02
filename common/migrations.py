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

from common.migration_mechanism import taserver_migration, upgrades_all_players
import json
from pathlib import Path

# Writing a migration function
#
# A migration function should be decorated with @taserver_migration(schema_version=n),
# where n = the version this migration will upgrade to
#
# If a migration fails, it should raise a ValueError (if it encounters a format error in existing data)
# or an OSError (if file system manipulation fails)
#
# The function it decorates should take one parameter, the path to where the data is stored. It is an arbitrary script
# that should perform whatever operations are needed for this migration
#
# A helper decoration, @upgrades_all_players, is provided to simplify migrations which upgrade
# the format of player datastores. See the docstring for that decorator for details of its contract
#
# Contract for the code running migrations:
# 1) If migrations succeed, then the code may rely on all datastores being at the schema version for which
#    there is the latest defined migration
# 2) Code must handle ValueErrors (format violations in the data) and OSErrors (assorted IO errors)
#
# Examples:
# @taserver_migration(schema_version=1)
# def _migration_1(data_root: str):
#     print('Performing migration on data root: %s' % data_root)
#     # Do migration
#
# @taserver_migration(schema_version=2)
# @upgrades_all_players()
# def _migration_2(data, player: str):
#     print('Performing pure migration for player: %s' % player)
#     # Transform data in some way
#     return data


@taserver_migration(schema_version=1)
@upgrades_all_players()
def _migration_ootb_and_goty_loadouts(data, player: str):
    if 'loadouts' not in data:
        # Uninitialised loadouts, don't migrate
        return data

    # Test to determine whether existing loadouts are 'ootb' or 'goty'
    # We can only migrate OOTB loadouts since there are now 9 loadouts per goty class
    # If the tertiary weapon slot (used for perks in GOTY) is >= 100000 then it is goty
    if data['loadouts']['1683']['0']['1765'] < 100000:
        data['ootb_loadouts'] = data['loadouts']

    del data['loadouts']

    return data


@taserver_migration(schema_version=2)
@upgrades_all_players()
def _migration_to_valid_clan_tags(data, player: str):
    if 'settings' not in data:
        return data

    if 'clan_tag' not in data['settings']:
        return data

    try:
        ascii_bytes = data['settings']['clan_tag'].encode('ascii')
    except UnicodeError:
        data['settings']['clan_tag'] = ''
    else:
        valid_bytes = bytes([c if (33 <= c <= 126 and chr(c) not in r'#/:?\`~') else ord('.') for c in ascii_bytes[:4]])
        data['settings']['clan_tag'] = valid_bytes.decode('ascii')

    return data


@taserver_migration(schema_version=3)
def _migration_adding_email_hash_to_accounts(data_root: str):
    path_to_account_database = Path(data_root)/'accountdatabase.json'
    with open(path_to_account_database, 'r') as f:
        accountlist = json.load(f)

    for account in accountlist:
        if 'email_hash' in account:
            raise ValueError('Upgrading failed because the account database already had entries with an email_hash in them')
        account['email_hash'] = None
        account['authcode_time'] = None

    with open(path_to_account_database, 'w') as f:
        json.dump(accountlist, f, indent=4)
