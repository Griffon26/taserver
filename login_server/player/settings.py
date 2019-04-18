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

import json
from common.game_items import UNMODDED_GAME_SETTING_MODE
from common.statetracer import statetracer

defaults = {
    'clan_tag': '',
    'game_setting_mode': UNMODDED_GAME_SETTING_MODE
}


@statetracer('clan_tag', 'game_setting_mode')
class PlayerSettings:
    def __init__(self):
        self.clan_tag = None
        self.game_setting_mode = None
        self.init_settings_from_dict({})

    def init_settings_from_dict(self, d):
        for key in defaults:
            setattr(self, key, d.get(key, defaults[key]))

    def load(self, filename):
        try:
            with open(filename, 'rt') as infile:
                d = json.load(infile)
        except OSError:
            d = {}

        self.init_settings_from_dict(d)

    def save(self, filename):
        current_values = {key: getattr(self, key) for key in defaults}
        with open(filename, 'wt') as outfile:
            json.dump(current_values, outfile, indent=4, sort_keys=True)
