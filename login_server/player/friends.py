#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>
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

import json
from common.migration_mechanism import SCHEMA_VERSION_KEY

FRIEND_STATE_VISIBLE = 0x00000001
FRIEND_STATE_ONLINE = 0x00001000
FRIEND_STATE_IN_GAME = 0x00002000

class Friends:

    def __init__(self):
        self.friends_dict = {}

    def add(self, unique_id, login_name):
        self.friends_dict[unique_id] = { 'login_name' : login_name }

    def remove(self, unique_id):
        self.friends_dict.pop(unique_id, None)

    def load(self, filename):
        try:
            with open(filename, 'rt') as infile:
                friend_dict_with_string_keys = json.load(infile)
                if SCHEMA_VERSION_KEY in friend_dict_with_string_keys:
                    del friend_dict_with_string_keys[SCHEMA_VERSION_KEY]
                self.friends_dict = {int(k): v for k, v in friend_dict_with_string_keys.items()}
        except OSError:
            self.friends_dict = {}

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump({**{str(k): v for k, v in self.friends_dict.items()}, SCHEMA_VERSION_KEY: 0}, outfile, indent=4, sort_keys=True)

