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

class MenuSettings:
    def __init__(self):
        self.settings_dict = {}

    def is_menu_setting(self, value):
        return value in self.loadout_id2key

    def load(self, filename):
        def json_keys_to_int(x):
            if isinstance(x, dict):
                return {int(k): v for k, v in x.items()}

        try:
            with open(filename, 'rt') as infile:
                self.settings_dict = json.load(infile, object_hook=json_keys_to_int)
        except OSError:
            self.settings_dict = self.defaults()

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump(self.settings_dict, outfile, indent=4, sort_keys=True)
