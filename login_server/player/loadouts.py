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

from ..datatypes import *

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
        MENU_AREA_LIGHT_LOADOUT_A: (LIGHT_CLASS, 0),
        MENU_AREA_LIGHT_LOADOUT_B: (LIGHT_CLASS, 1),
        MENU_AREA_LIGHT_LOADOUT_C: (LIGHT_CLASS, 2),
        MENU_AREA_LIGHT_LOADOUT_D: (LIGHT_CLASS, 3),
        MENU_AREA_LIGHT_LOADOUT_E: (LIGHT_CLASS, 4),
        MENU_AREA_LIGHT_LOADOUT_F: (LIGHT_CLASS, 5),
        MENU_AREA_LIGHT_LOADOUT_G: (LIGHT_CLASS, 6),
        MENU_AREA_LIGHT_LOADOUT_H: (LIGHT_CLASS, 7),
        MENU_AREA_LIGHT_LOADOUT_I: (LIGHT_CLASS, 8),

        MENU_AREA_HEAVY_LOADOUT_A: (HEAVY_CLASS, 0),
        MENU_AREA_HEAVY_LOADOUT_B: (HEAVY_CLASS, 1),
        MENU_AREA_HEAVY_LOADOUT_C: (HEAVY_CLASS, 2),
        MENU_AREA_HEAVY_LOADOUT_D: (HEAVY_CLASS, 3),
        MENU_AREA_HEAVY_LOADOUT_E: (HEAVY_CLASS, 4),
        MENU_AREA_HEAVY_LOADOUT_F: (HEAVY_CLASS, 5),
        MENU_AREA_HEAVY_LOADOUT_G: (HEAVY_CLASS, 6),
        MENU_AREA_HEAVY_LOADOUT_H: (HEAVY_CLASS, 7),
        MENU_AREA_HEAVY_LOADOUT_I: (HEAVY_CLASS, 8),

        MENU_AREA_MEDIUM_LOADOUT_A: (MEDIUM_CLASS, 0),
        MENU_AREA_MEDIUM_LOADOUT_B: (MEDIUM_CLASS, 1),
        MENU_AREA_MEDIUM_LOADOUT_C: (MEDIUM_CLASS, 2),
        MENU_AREA_MEDIUM_LOADOUT_D: (MEDIUM_CLASS, 3),
        MENU_AREA_MEDIUM_LOADOUT_E: (MEDIUM_CLASS, 4),
        MENU_AREA_MEDIUM_LOADOUT_F: (MEDIUM_CLASS, 5),
        MENU_AREA_MEDIUM_LOADOUT_G: (MEDIUM_CLASS, 6),
        MENU_AREA_MEDIUM_LOADOUT_H: (MEDIUM_CLASS, 7),
        MENU_AREA_MEDIUM_LOADOUT_I: (MEDIUM_CLASS, 8),
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

