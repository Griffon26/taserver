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


class PlayerSettings:

    def __init__(self):
        self.game_setting_mode = 'ootb'

    def load(self, filename):
        try:
            with open(filename, 'rt') as infile:
                d = json.load(infile)
                self.game_setting_mode = d.get('game_setting_mode', 'ootb')
        except OSError:
            self.game_setting_mode = 'ootb'

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump(vars(self), outfile, indent=4, sort_keys=True)
