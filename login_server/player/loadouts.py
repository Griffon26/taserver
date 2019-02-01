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

from typing import List, Dict
import json

from common.game_items import game_classes, get_game_setting_modes
from common.datatypes import *

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
        self.loadout_dict = self.fill_in_defaults(dict())

    def get_loadouts(self, game_setting_mode: str):
        return self.loadout_dict[game_setting_mode]

    def fill_in_defaults(self, existing_loadouts):
        result = dict()
        for game_setting_mode in get_game_setting_modes():
            print('Setting up loadouts for... %s' % game_setting_mode)
            if len(existing_loadouts.get(game_setting_mode, dict())) == 0:
                # No existing loadouts for this game setting mode, set defaults
                print('No loadouts found for %s' % game_setting_mode)
                default_loadouts_file = 'data/defaults/default_loadouts_%s.json' % game_setting_mode
                result[game_setting_mode] = self._load_loadout_data(default_loadouts_file)
            else:
                result[game_setting_mode] = existing_loadouts[game_setting_mode]
        return result

    def is_loadout_menu_item(self, value):
        return value in self.loadout_id2key

    def modify(self, game_setting_mode: str, loadout_id, slot, equipment):
        class_id, loadout_index = self.loadout_id2key[loadout_id]
        d = self.loadout_dict[game_setting_mode]
        d[class_id][loadout_index][slot] = equipment

    def modify_by_class_details(self, game_setting_mode: str, class_id: int,
                                loadout_num: int, slot: int, equipment: int):
        loadout_id = self.loadout_key2id[(class_id, loadout_num)]
        self.modify(game_setting_mode, loadout_id, slot, equipment)

    def strip_loadouts_for_modded_menus(self, game_setting_mode: str) -> List[Dict]:
        result = list()

        for class_id, class_defs in self.loadout_dict[game_setting_mode].items():
            for loadout_index, loadout_def in class_defs.items():
                result.extend({'class': class_id, 'num': loadout_index, 'eqp': slot, 'item': item}
                              for slot, item
                              in loadout_def.items())

        return result

    def _load_loadout_data(self, filename):
        def json_keys_to_int(x):
            if isinstance(x, dict):
                return {(int(k) if k not in get_game_setting_modes() else k): v
                        for k, v
                        in x.items()}

        with open(filename, 'rt') as infile:
            return json.load(infile, object_hook=json_keys_to_int)

    def load(self, filename):
        try:
            self.loadout_dict = self.fill_in_defaults(self._load_loadout_data(filename))
        except OSError:
            self.loadout_dict = self.fill_in_defaults(dict())

    def save(self, filename):
        with open(filename, 'wt') as outfile:
            json.dump(self.loadout_dict, outfile, indent=4, sort_keys=True)
