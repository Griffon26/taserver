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

LIGHT_CLASS = 1683
MEDIUM_CLASS = 1693
HEAVY_CLASS = 1692

SLOT_PRIMARY_WEAPON = 1086
SLOT_SECONDARY_WEAPON = 1087
SLOT_TERTIARY_WEAPON = 1765
SLOT_PACK = 1088
SLOT_BELT = 1089
SLOT_SKIN = 1093
SLOT_VOICE = 1094

EQUIPMENT_SPINFUSOR = 7401
EQUIPMENT_LIGHT_SPINFUSOR = 7422
EQUIPMENT_LIGHT_ASSAULT_RIFLE = 7438
EQUIPMENT_HEAVY_SPINFUSOR = 7448
EQUIPMENT_THRUST_PACK = 7822
EQUIPMENT_IMPACT_NITRON = 7387
EQUIPMENT_PATHFINDER_SKIN = 7834
EQUIPMENT_LIGHT_VOICE = 8666
EQUIPMENT_MEDIUM_VOICE = 8667
EQUIPMENT_HEAVY_VOICE = 8668
EQUIPMENT_LIGHT_GRENADE_LAUNCHER = 8761


class Loadouts:
    loadout_id2key = {
        0x02990EE4: (LIGHT_CLASS, 0),
        0x02990EE5: (LIGHT_CLASS, 1),
        0x02990EE6: (LIGHT_CLASS, 2),
        0x02990EE7: (LIGHT_CLASS, 3),
        0x02990EE8: (LIGHT_CLASS, 4),
        0x02990EE9: (LIGHT_CLASS, 5),
        0x02990EEA: (LIGHT_CLASS, 6),
        0x02990EEB: (LIGHT_CLASS, 7),
        0x02990EEC: (LIGHT_CLASS, 8),

        0x02990EED: (HEAVY_CLASS, 0),
        0x02990EEE: (HEAVY_CLASS, 1),
        0x02990EEF: (HEAVY_CLASS, 2),
        0x02990EF0: (HEAVY_CLASS, 3),
        0x02990EF1: (HEAVY_CLASS, 4),
        0x02990EF2: (HEAVY_CLASS, 5),
        0x02990EF3: (HEAVY_CLASS, 6),
        0x02990EF4: (HEAVY_CLASS, 7),
        0x02990EF5: (HEAVY_CLASS, 8),

        0x02990EF6: (MEDIUM_CLASS, 0),
        0x02990EF7: (MEDIUM_CLASS, 1),
        0x02990EF8: (MEDIUM_CLASS, 2),
        0x02990EF9: (MEDIUM_CLASS, 3),
        0x02990EFA: (MEDIUM_CLASS, 4),
        0x02990EFB: (MEDIUM_CLASS, 5),
        0x02990EFC: (MEDIUM_CLASS, 6),
        0x02990EFD: (MEDIUM_CLASS, 7),
        0x02990EFE: (MEDIUM_CLASS, 8),
    }
    loadout_key2id = {v: k for k, v in loadout_id2key.items()}

    def __init__(self):
        self.loadout_dict = self.defaults()

    def defaults(self):
        default_light_loadout = {
            SLOT_PRIMARY_WEAPON: EQUIPMENT_LIGHT_SPINFUSOR,
            SLOT_SECONDARY_WEAPON: EQUIPMENT_LIGHT_SPINFUSOR,
            SLOT_TERTIARY_WEAPON: EQUIPMENT_LIGHT_SPINFUSOR,
            SLOT_PACK: EQUIPMENT_THRUST_PACK,
            SLOT_BELT: EQUIPMENT_IMPACT_NITRON,
            SLOT_SKIN: EQUIPMENT_PATHFINDER_SKIN,
            SLOT_VOICE: EQUIPMENT_LIGHT_VOICE
        }

        default_medium_loadout = {
            SLOT_PRIMARY_WEAPON: EQUIPMENT_SPINFUSOR,
            SLOT_SECONDARY_WEAPON: EQUIPMENT_SPINFUSOR,
            SLOT_TERTIARY_WEAPON: EQUIPMENT_SPINFUSOR,
            SLOT_PACK: EQUIPMENT_THRUST_PACK,
            SLOT_BELT: EQUIPMENT_IMPACT_NITRON,
            SLOT_SKIN: EQUIPMENT_PATHFINDER_SKIN,
            SLOT_VOICE: EQUIPMENT_MEDIUM_VOICE
        }

        default_heavy_loadout = {
            SLOT_PRIMARY_WEAPON: EQUIPMENT_HEAVY_SPINFUSOR,
            SLOT_SECONDARY_WEAPON: EQUIPMENT_HEAVY_SPINFUSOR,
            SLOT_TERTIARY_WEAPON: EQUIPMENT_HEAVY_SPINFUSOR,
            SLOT_PACK: EQUIPMENT_THRUST_PACK,
            SLOT_BELT: EQUIPMENT_IMPACT_NITRON,
            SLOT_SKIN: EQUIPMENT_PATHFINDER_SKIN,
            SLOT_VOICE: EQUIPMENT_HEAVY_VOICE
        }

        max_loadouts = 9

        default_loadouts = {
            LIGHT_CLASS: {i: dict(default_light_loadout) for i in range(max_loadouts)},
            MEDIUM_CLASS: {i: dict(default_medium_loadout) for i in range(max_loadouts)},
            HEAVY_CLASS: {i: dict(default_heavy_loadout) for i in range(max_loadouts)}
        }

        return default_loadouts

    def is_loadout_menu_item(self, value):
        return value in self.loadout_id2key

    def modify(self, loadout_id, slot, equipment):
        class_id, loadout_index = self.loadout_id2key[loadout_id]
        self.loadout_dict[class_id][loadout_index][slot] = equipment

    def load(self, filename):
        def json_keys_to_int(x):
            if isinstance(x, dict):
                return {int(k): v for k, v in x.items()}

        try:
            with open(filename, 'rt') as infile:
                self.loadout_dict = json.load(infile, object_hook=json_keys_to_int)
        except OSError:
            self.loadout_dict = self.defaults()

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump(self.loadout_dict, outfile, indent=4, sort_keys=True)

