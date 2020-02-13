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
import datetime
from common.game_items import UNMODDED_GAME_SETTING_MODE
from common.statetracer import statetracer

DEFAULT_LAST_WIN_DATETIME = datetime.datetime(1970, 1, 1)
BASE_XP_PER_SECOND = 0.5833
FIRST_WIN_XP_BONUS = 1200


class PlayerProgression:
    def __init__(self, rank_xp=0, last_first_win_time=DEFAULT_LAST_WIN_DATETIME):
        self.rank_xp = rank_xp
        self.last_first_win_time = last_first_win_time

    def is_eligible_for_first_win(self) -> bool:
        # Eligible for first win after midnight of every day
        next_eligible_date = self.last_first_win_time.date() + datetime.timedelta(days=1)
        next_eligible_time = datetime.datetime.combine(next_eligible_date, datetime.time(0, 0, 0))
        return datetime.datetime.utcnow() > next_eligible_time

    def earn_xp(self, time_played: int, was_win: bool) -> None:
        # Base XP (purely from time played)
        xp_earned = time_played * BASE_XP_PER_SECOND

        # First Win of the Day bonus
        if self.is_eligible_for_first_win() and was_win:
            xp_earned += FIRST_WIN_XP_BONUS
            self.last_first_win_time = datetime.datetime.utcnow()

        # Round down, XP must be an integer value
        xp_earned = int(xp_earned)

        self.rank_xp += xp_earned

    @classmethod
    def from_dict(cls, d):
        last_first_win_time = DEFAULT_LAST_WIN_DATETIME
        if 'last_first_win_time' in d:
            try:
                last_first_win_time = datetime.datetime.strptime(d['last_first_win_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                # Ignore invalid last first win time
                pass
        return cls(d.get('rank_xp', 0), last_first_win_time)

    def to_dict(self):
        return {
            'rank_xp': self.rank_xp,
            'last_first_win_time': self.last_first_win_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }


defaults = {
    'clan_tag': '',
    'game_setting_mode': UNMODDED_GAME_SETTING_MODE,
    'progression': dict()
}

load_transforms = {
    'progression': PlayerProgression.from_dict
}

save_transforms = {
    'progression': PlayerProgression.to_dict
}


@statetracer('clan_tag', 'game_setting_mode')
class PlayerSettings:
    def __init__(self):
        self.clan_tag = None
        self.game_setting_mode = None
        self.progression = {}
        self.init_settings_from_dict({})

    def init_settings_from_dict(self, d):
        for key in defaults:
            val = d.get(key, defaults[key])
            if key in load_transforms:
                val = load_transforms[key](val)
            setattr(self, key, val)

    def load(self, filename):
        try:
            with open(filename, 'rt') as infile:
                d = json.load(infile)
        except OSError:
            d = {}

        self.init_settings_from_dict(d)

    def save(self, filename):
        current_values = {key: getattr(self, key) for key in defaults}
        for key, transform in save_transforms.items():
            current_values[key] = transform(current_values[key])
        with open(filename, 'wt') as outfile:
            json.dump(current_values, outfile, indent=4, sort_keys=True)
