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
import string

from common.game_items import game_classes, do_use_goty_defs
from ..datatypes import *

SLOT_LOADOUT_NAME = 1341
SLOT_PRIMARY_WEAPON = 1086
SLOT_SECONDARY_WEAPON = 1087
SLOT_TERTIARY_WEAPON = 1765
SLOT_PACK = 1088
SLOT_BELT = 1089
SLOT_SKIN = 1093
SLOT_VOICE = 1094

EQUIPMENT_ASSAULT_RIFLE = 7385
EQUIPMENT_CHAINGUN = 7386
EQUIPMENT_FRAG_GRENADES = 7390
EQUIPMENT_FUSION_MORTAR = 7393
EQUIPMENT_SPINFUSOR = 7401
EQUIPMENT_THUMPERD = 7462
EQUIPMENT_GRENADE_LAUNCHER = 7416
EQUIPMENT_LIGHT_SPINFUSOR = 7422
EQUIPMENT_AP_GRENADES = 7434
EQUIPMENT_HEAVYAP_GRENADES = 7447
EQUIPMENT_FRAGXL_GRENADES = 7430
EQUIPMENT_LIGHT_ASSAULT_RIFLE = 7438
EQUIPMENT_BXT1 = 7400
EQUIPMENT_FALCON = 7419
EQUIPMENT_T5_GRENADES = 7914
EQUIPMENT_ENERGY_PACK = 7900
EQUIPMENT_HEAVY_SPINFUSOR = 7448
EQUIPMENT_SPINFUSOR_MKD = 7446
EQUIPMENT_LONG_RANGE_REPAIR_TOOL = 8405
EQUIPMENT_THRUST_PACK = 7822
EQUIPMENT_IMPACT_NITRON = 7387
EQUIPMENT_HEAVY_SHIELD_PACK = 7826
EQUIPMENT_JUG_REGEN_PACK = 7831
EQUIPMENT_SHIELD_PACK = 7832
EQUIPMENT_SLD_ENERGY_PACK = 7824
EQUIPMENT_PATHFINDER_SKIN = 7834
EQUIPMENT_SENTINEL_SKIN = 8327
EQUIPMENT_SOLDIER_SKIN = 8328
EQUIPMENT_JUGGERNAUT_SKIN = 8331
EQUIPMENT_LIGHT_VOICE = 8666
EQUIPMENT_MEDIUM_VOICE = 8667
EQUIPMENT_HEAVY_VOICE = 8668
EQUIPMENT_LIGHT_GRENADE_LAUNCHER = 8761

EQUIPMENT_PERKS_ULTRACAP_DETERMINATION = 535109597

default_loadouts_ootb = {
    'light': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_LIGHT_SPINFUSOR,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_LIGHT_ASSAULT_RIFLE,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_LIGHT_GRENADE_LAUNCHER,
        SLOT_PACK: EQUIPMENT_THRUST_PACK,
        SLOT_BELT: EQUIPMENT_IMPACT_NITRON,
        SLOT_SKIN: EQUIPMENT_PATHFINDER_SKIN,
        SLOT_VOICE: EQUIPMENT_LIGHT_VOICE
    },
    'medium': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_SPINFUSOR,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_ASSAULT_RIFLE,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_GRENADE_LAUNCHER,
        SLOT_PACK: EQUIPMENT_SHIELD_PACK,
        SLOT_BELT: EQUIPMENT_AP_GRENADES,
        SLOT_SKIN: EQUIPMENT_SOLDIER_SKIN,
        SLOT_VOICE: EQUIPMENT_MEDIUM_VOICE
    },
    'heavy': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_HEAVY_SPINFUSOR,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_FUSION_MORTAR,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_CHAINGUN,
        SLOT_PACK: EQUIPMENT_HEAVY_SHIELD_PACK,
        SLOT_BELT: EQUIPMENT_FRAG_GRENADES,
        SLOT_SKIN: EQUIPMENT_JUGGERNAUT_SKIN,
        SLOT_VOICE: EQUIPMENT_HEAVY_VOICE
    }
}

default_loadouts_goty = {
    'light': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_LIGHT_SPINFUSOR,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_LIGHT_ASSAULT_RIFLE,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_PERKS_ULTRACAP_DETERMINATION,
        SLOT_PACK: EQUIPMENT_THRUST_PACK,
        SLOT_BELT: EQUIPMENT_IMPACT_NITRON,
        SLOT_SKIN: EQUIPMENT_PATHFINDER_SKIN,
        SLOT_VOICE: EQUIPMENT_LIGHT_VOICE
    },
    'medium': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_ASSAULT_RIFLE,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_THUMPERD,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_PERKS_ULTRACAP_DETERMINATION,
        SLOT_PACK: EQUIPMENT_SLD_ENERGY_PACK,
        SLOT_BELT: EQUIPMENT_FRAGXL_GRENADES,
        SLOT_SKIN: EQUIPMENT_SOLDIER_SKIN,
        SLOT_VOICE: EQUIPMENT_MEDIUM_VOICE
    },
    'heavy': {
        SLOT_PRIMARY_WEAPON: EQUIPMENT_FUSION_MORTAR,
        SLOT_SECONDARY_WEAPON: EQUIPMENT_SPINFUSOR_MKD,
        SLOT_TERTIARY_WEAPON: EQUIPMENT_PERKS_ULTRACAP_DETERMINATION,
        SLOT_PACK: EQUIPMENT_JUG_REGEN_PACK,
        SLOT_BELT: EQUIPMENT_HEAVYAP_GRENADES,
        SLOT_SKIN: EQUIPMENT_JUGGERNAUT_SKIN,
        SLOT_VOICE: EQUIPMENT_HEAVY_VOICE
    }
}


class Loadouts:
    max_loadouts = 9

    loadout_id2key = {
        MENU_AREA_LIGHT_LOADOUT_A: (game_classes['light'].class_id, 0),
        MENU_AREA_LIGHT_LOADOUT_B: (game_classes['light'].class_id, 1),
        MENU_AREA_LIGHT_LOADOUT_C: (game_classes['light'].class_id, 2),
        MENU_AREA_LIGHT_LOADOUT_D: (game_classes['light'].class_id, 3),
        MENU_AREA_LIGHT_LOADOUT_E: (game_classes['light'].class_id, 4),
        MENU_AREA_LIGHT_LOADOUT_F: (game_classes['light'].class_id, 5),
        MENU_AREA_LIGHT_LOADOUT_G: (game_classes['light'].class_id, 6),
        MENU_AREA_LIGHT_LOADOUT_H: (game_classes['light'].class_id, 7),
        MENU_AREA_LIGHT_LOADOUT_I: (game_classes['light'].class_id, 8),

        MENU_AREA_HEAVY_LOADOUT_A: (game_classes['medium'].class_id, 0),
        MENU_AREA_HEAVY_LOADOUT_B: (game_classes['medium'].class_id, 1),
        MENU_AREA_HEAVY_LOADOUT_C: (game_classes['medium'].class_id, 2),
        MENU_AREA_HEAVY_LOADOUT_D: (game_classes['medium'].class_id, 3),
        MENU_AREA_HEAVY_LOADOUT_E: (game_classes['medium'].class_id, 4),
        MENU_AREA_HEAVY_LOADOUT_F: (game_classes['medium'].class_id, 5),
        MENU_AREA_HEAVY_LOADOUT_G: (game_classes['medium'].class_id, 6),
        MENU_AREA_HEAVY_LOADOUT_H: (game_classes['medium'].class_id, 7),
        MENU_AREA_HEAVY_LOADOUT_I: (game_classes['medium'].class_id, 8),

        MENU_AREA_MEDIUM_LOADOUT_A: (game_classes['heavy'].class_id, 0),
        MENU_AREA_MEDIUM_LOADOUT_B: (game_classes['heavy'].class_id, 1),
        MENU_AREA_MEDIUM_LOADOUT_C: (game_classes['heavy'].class_id, 2),
        MENU_AREA_MEDIUM_LOADOUT_D: (game_classes['heavy'].class_id, 3),
        MENU_AREA_MEDIUM_LOADOUT_E: (game_classes['heavy'].class_id, 4),
        MENU_AREA_MEDIUM_LOADOUT_F: (game_classes['heavy'].class_id, 5),
        MENU_AREA_MEDIUM_LOADOUT_G: (game_classes['heavy'].class_id, 6),
        MENU_AREA_MEDIUM_LOADOUT_H: (game_classes['heavy'].class_id, 7),
        MENU_AREA_MEDIUM_LOADOUT_I: (game_classes['heavy'].class_id, 8),
    }

    loadout_key2id = {v: k for k, v in loadout_id2key.items()}

    def __init__(self):
        self.loadout_dict = self.defaults()

    def defaults(self):
        def finish_default_loadout(default_loadout, i):
            complete_loadout = default_loadout.copy()
            complete_loadout[SLOT_LOADOUT_NAME] = 'LOADOUT %s' % string.ascii_uppercase[i]
            return complete_loadout

        default_loadouts = default_loadouts_goty if do_use_goty_defs else default_loadouts_ootb
        return {game_classes[name].class_id:
                {i: finish_default_loadout(default_loadout, i) for i in range(self.max_loadouts)}
                for name, default_loadout
                in default_loadouts.items()}

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
