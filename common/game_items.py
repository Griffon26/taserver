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

from typing import NamedTuple, Dict, Set, List, Tuple, Generator


class GamePurchase:
    """
    Data about an in-game purchase of any kind
    """

    item_kind_id = 0x0

    def __init__(self, name: str, item_id: int, shown: bool):
        self.name = name
        self.item_id = item_id
        self.shown = shown

    def __repr__(self):
        return f'GamePurchase("{self.name}", {self.item_id}, {self.shown})'


class GameClass:
    """
    Data about an in-game class
    """

    def __init__(self, class_id: int, secondary_id: int, family_info_name: str,
                 short_name: str, purchase_name: str, is_ootb: bool):
        self.class_id = class_id
        self.secondary_id = secondary_id
        self.family_info_name = family_info_name
        self.short_name = short_name
        self.purchase_name = purchase_name
        self.is_ootb = is_ootb

    def __hash__(self):
        return self.class_id.__hash__()

    def __repr__(self):
        return f'GameClass({self.class_id}, {self.secondary_id}, "{self.family_info_name}", ' \
               f'"{self.short_name}", "{self.purchase_name}")'


class UnlockableGameClass(GamePurchase):
    """
    Data and state for an in-game unlockable class
    """

    item_kind_id = 0x27a5

    def __init__(self, game_class: GameClass, shown: bool = True):
        super().__init__(game_class.purchase_name, game_class.class_id, shown)
        self.game_class = game_class


class UnlockableItem(GamePurchase):
    """
    Data and state for unlockable in-game item of any kind
    """

    def __init__(self, name: str, item_id: int, shown: bool = True, unlocked: bool = True,
                 is_ootb: bool = True) -> None:
        super().__init__(name, item_id, shown)
        self.unlocked = unlocked
        self.is_ootb = is_ootb

    def __hash__(self):
        return self.item_id.__hash__()

    def __repr__(self):
        return f'UnlockableItem("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


class UnlockableClassSpecificItem(UnlockableItem):
    """
    An unlockable in-game item tied to a specific class
    """

    item_kind_id = 0x00D9

    def __init__(self, name: str, item_id: int, game_class: GameClass, shown: bool = True, unlocked: bool = True,
                 is_ootb: bool = True) -> None:
        super().__init__(name, item_id, shown, unlocked, is_ootb)
        self.game_class = game_class

    def __repr__(self):
        return f'UnlockableClassSpecificItem("{self.name}", {self.item_id}, ' \
               f'{self.game_class.class_id}, {self.shown}, {self.unlocked})'


class UnlockableWeapon(UnlockableClassSpecificItem):
    """
    An unlockable in-game weapon
    """

    def __init__(self, name: str, item_id: int, game_class: GameClass,
                 category: int, shown: bool = True, unlocked: bool = True, is_ootb: bool = True) -> None:
        super().__init__(name, item_id, game_class, shown, unlocked, is_ootb)
        self.category = category

    def __repr__(self):
        return f'UnlockableWeapon("{self.name}", {self.item_id}, ' \
               f'{self.game_class.class_id}, {self.category}, {self.shown}, {self.unlocked})'


class UnlockablePack(UnlockableClassSpecificItem):
    """
    An unlockable in-game pack
    """

    item_kind_id = 0x28AD


class UnlockableSkin(UnlockableClassSpecificItem):
    """
    An unlockable in-game skin
    """

    item_kind_id = 0x03B6


class UnlockableVoice(UnlockableItem):
    """
    An unlockable in-game voice, not specific to a class
    """
    item_kind_id = 0x03B6

    def __repr__(self):
        return f'UnlockableVoice("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


class ClassUnlockables(NamedTuple):
    """
    Definition of the intended state of a class in the loadout menus
    """
    weapons: List[UnlockableWeapon]
    belt_items: List[UnlockableClassSpecificItem]
    packs: List[UnlockablePack]
    skins: List[UnlockableSkin]


class Unlockables(NamedTuple):
    """
    Definition of the intended state of the whole loadout menu
    """
    classes: Dict[str, GameClass]  # Valid in-game classes
    class_purchases: Set[UnlockableGameClass]
    categories: Dict[str, Dict[str, int]]
    class_items: Dict[GameClass, ClassUnlockables]
    voices: Set[UnlockableVoice]

    def get_every_item(self) -> List[UnlockableItem]:
        """
        :return: a flattened list of every unlockable item
        """
        items = []
        for _, c in self.class_items.items():
            items.extend(c.weapons)
            items.extend(c.belt_items)
            items.extend(c.packs)
            items.extend(c.skins)
        items.extend(self.voices)
        return items


def get_items_generator(items: Dict[str, Dict[str, int]]) -> Generator[Tuple[str, int, bool], None, None]:
    """
    Generator which converts a structure defining weapons under 'ootb' and other categories
    to an iterable of items augmented with status of whether or not they are OOTB items

    :param items: mapping of weapon origin - 'ootb' or another, to weapon name -> id mappings
    :return: yields each item in turn, with a boolean indicating whether it is an OOTB item
    """
    for sect_name, section in items.items():
        for item_name, item_id in section.items():
            yield item_name, item_id, sect_name.lower() == 'ootb'


def process_class_items(game_class: GameClass, categories: Dict[str, Dict[str, int]], items_def: Dict,
                        removals: Set[str], locked: Set[str], non_ootb_unlocked: bool) -> ClassUnlockables:
    """
    Process a hierarchical definition of a class's items into a ClassUnlockables structure

    :param game_class: the game class
    :param categories: mapping of classes to the mappings of categories of weapons for each class
    :param items_def: hierarchical items definition
    :param removals: list of item names to remove (not show at all in the menu)
    :param locked: list of item names to show locked in the menu
    :param non_ootb_unlocked: whether items not marked as OOTB should be unlocked
    :return: the resulting ClassUnlockables
    """
    # Weapons
    weapons = [UnlockableWeapon(item_name, item_id,
                                game_class, categories[game_class.short_name][category_name],
                                item_name not in removals,
                                item_name not in locked and (is_ootb or non_ootb_unlocked), is_ootb)
               for category_name, category_def
               in items_def['weapons'].items()
               for item_name, item_id, is_ootb
               in get_items_generator(category_def)]

    # Belt
    belt = [UnlockableClassSpecificItem(item_name, item_id, game_class,
                                        item_name not in removals,
                                        item_name not in locked and (is_ootb or non_ootb_unlocked), is_ootb)
            for item_name, item_id, is_ootb
            in get_items_generator(items_def['belt'])]

    # Packs
    packs = [UnlockablePack(item_name, item_id, game_class,
                            item_name not in removals,
                            item_name not in locked and (is_ootb or non_ootb_unlocked), is_ootb)
             for item_name, item_id, is_ootb
             in get_items_generator(items_def['packs'])]

    # Skins
    skins = [UnlockableSkin(item_name, item_id, game_class,
                            item_name not in removals,
                            item_name not in locked and (is_ootb or non_ootb_unlocked), is_ootb)
             for item_name, item_id, is_ootb
             in get_items_generator(items_def['skins'])]

    return ClassUnlockables(weapons, belt, packs, skins)


def build_class_menu_data(classes: Dict[str, GameClass],
                          categories: Dict[str, Dict[str, int]],
                          definitions: Dict,
                          removals: Set[str],
                          locked: Set[str],
                          non_ootb_classes: bool,
                          non_ootb_unlocked: bool) -> Unlockables:
    """
    Process a full hierarchical definition of the item menus into a structured Unlockables object

    :param classes: mapping of game class names to GameClass definitions
    :param categories: mapping of class names to the mappings of categories of weapons for each class
    :param definitions: the original hierarchical definition of the menus
    :param removals: list of item names to remove (not show at all in the menu)
    :param locked: list of item names to show locked in the menu
    :param non_ootb_classes: whether classes not marked as OOTB should be shown
    :param non_ootb_unlocked: whether items not marked as OOTB should be unlocked
    :return: the resulting Unlockables object
    """
    enabled_classes = {n: c for n, c in classes.items() if c.is_ootb or non_ootb_classes}

    class_purchases = {UnlockableGameClass(game_class, game_class.is_ootb or non_ootb_classes)
                       for name, game_class
                       in enabled_classes.items()}

    voices = {UnlockableVoice(name, item_id,
                              name not in removals, name not in locked and (is_ootb or non_ootb_unlocked), is_ootb)
              for name, item_id, is_ootb
              in get_items_generator(definitions['voices'])}

    class_items = {game_class: process_class_items(game_class, categories,
                                                   definitions['classes'][class_name],
                                                   removals, locked, non_ootb_unlocked)
                   for class_name, game_class
                   in enabled_classes.items()}

    unlockables = Unlockables(enabled_classes, class_purchases, categories, class_items, voices)

    return unlockables


# Definition of the game class info; the class name keys should match weapon_categories and hierarchical_definitions
game_classes: Dict[str, GameClass] = {
    'pathfinder': GameClass(1683, 101330, 'TrFamilyInfo_Light_Pathfinder', 'pathfinder', "Pathfinder Purchase", True),
    'sentinel': GameClass(1686, 101331, 'TrFamilyInfo_Light_Sentinel', 'sentinel', "Sentinel Purchase", True),
    'soldier': GameClass(1693, 101342, 'TrFamilyInfo_Medium_Soldier', 'soldier', "Soldier Purchase", True),
    'juggernaught': GameClass(1692, 101341, 'TrFamilyInfo_Heavy_Juggernaught', 'juggernaught', "Juggernaught Purchase", True),
}

# Definition of the weapon categories; category names should match hierarchical_definitions
weapon_categories: Dict[str, Dict[str, int]] = {
    'pathfinder': {
        'impact': 11126,
        'timed': 11142,
        'speciality': 11128,
        'bullet': 11127,
        'short_range': 11129
    },
    'sentinel': {
        'impact': 11126,
        'timed': 11142,
        'speciality': 11128,
        'bullet': 11127,
        'short_range': 11129
    },
    'soldier': {
        'impact': 11131,
        'timed': 11133,
        'speciality': 11135,
        'bullet': 11132,
        'short_range': 11143
    },
    'juggernaught': {
        'impact': 11136,
        'timed': 11139,
        'speciality': 11141,
        'bullet': 11137,
        'short_range': 11138
    },
}

# Definition of where items appear in the menu (including weapons going to be removed/locked)
# Moving items will change where the item appears in the menus, e.g. which class/category it is available to
hierarchical_definitions = {
    'classes': {
        'pathfinder': {
            'weapons': {
                'impact': {
                    'ootb': {
                        'Pathfinder_Primary_LightSpinfusor': 7422,
                        'Pathfinder_Primary_BoltLauncher': 7425,
                        'Pathfinder_Primary_LightSpinfusor_100X': 8696,
                        'Pathfinder_Primary_LightTwinfusor': 8245,
                    },
                    'other': {
                        'Pathfinder_Primary_LightSpinfusor_MKD': 8415,
                        'Infiltrator_Primary_StealthLightSpinfusor': 7902,
                    },
                },
                'timed': {
                    'ootb': {
                        'Light_Primary_LightGrenadeLauncher': 8761,
                        'Infiltrator_Primary_RemoteArxBuster': 8252,
                    },
                    'other': {},

                },
                'speciality': {
                    'ootb': {
                        'Sentinel_Primary_SniperRifle': 7400,
                        'Sentinel_Primary_PhaseRifle': 7395,
                    },
                    'other': {
                        'Sentinel_Primary_SniperRifle_MKD': 8407,
                        'Sentinel_Primary_SAP20': 8254,
                    },
                },
                'bullet': {
                    'ootb': {
                        'Pathfinder_Secondary_LightAssaultRifle': 7438,
                        'Sentinel_Secondary_Falcon': 7419,
                        'Light_Sidearm_Sparrow': 7433,
                        'Infiltrator_Secondary_ThrowingKnives': 8256,
                    },
                    'other': {
                        'Infiltrator_Primary_RhinoSMG': 7397,
                        'Infiltrator_Primary_RhinoSMG_MKD': 8409,
                        'Infiltrator_Secondary_SN7': 7418,
                        'Infiltrator_Secondary_SN7_MKD': 8404,
                    },
                },
                'short_range': {
                    'ootb': {
                        'Pathfinder_Secondary_Shotgun': 7399,
                        'All_H1_Shocklance': 7435,
                    },
                    'other': {
                        'Pathfinder_Secondary_Shotgun_MKD': 8411,
                        'Sentinel_Secondary_AccurizedShotgun': 8239,
                    },
                },
            },
            'belt': {
                'ootb': {
                    'Pathfinder_Belt_ImpactNitron': 7387,
                    'Pathfinder_Belt_STGrenade': 7437,
                    'Sentinel_Belt_GrenadeT5': 7914,
                    'Infiltrator_Belt_StickyGrenade': 7402,
                    'Sentinel_Belt_Claymore': 7421,
                    'Infiltrator_Belt_PrismMines': 7440,
                    'Infiltrator_Belt_NinjaSmoke': 8248,
                },
                'other': {
                    'Pathfinder_Belt_ImpactNitron_MKD': 8396,
                    'Infiltrator_Belt_StickyGrenade_MKD': 8398,
                    'Sentinel_Belt_ArmoredClaymore': 8240,
                },
            },
            'packs': {
                'ootb': {
                    'Pathfinder_Pack_JumpPack': 7822,
                    'Pathfinder_Pack_EnergyRecharge': 7825,
                    'Infiltrator_Pack_Stealth': 7833,
                },
                'other': {
                    'Sentinel_Pack_EnergyRecharge': 7900,
                    # 'Sentinel_Pack_DropJammer': 7456, # Repurposed as Drop Station
                },
            },
            'skins': {
                'ootb': {
                    'Skin PTH': 7834,
                    'Skin INF': 7835,
                    'Skin SEN': 8327,
                    'Skin PTH Mercenary': 8326,
                    'Skin INF Mercenary': 8336,
                    'Skin SEN Mercenary': 8337,
                    'Skin INF Assassin': 8665,
                },
                'other': {},
            }
        },
        'sentinel': {
            'weapons': {
                'impact': {
                    'ootb': {
                    },
                    'other': {
                    },
                },
                'timed': {
                    'ootb': {
                    },
                    'other': {},

                },
                'speciality': {
                    'ootb': {
                        'Sentinel_Primary_SniperRifle': 7400,
                        'Sentinel_Primary_PhaseRifle': 7395,
                    },
                    'other': {
                        'Sentinel_Primary_SniperRifle_MKD': 8407,
                        'Sentinel_Primary_SAP20': 8254,
                    },
                },
                'bullet': {
                    'ootb': {
                        'Sentinel_Secondary_Falcon': 7419,
                    },
                    'other': {
                    },
                },
                'short_range': {
                    'ootb': {
                    },
                    'other': {
                        'Sentinel_Secondary_AccurizedShotgun': 8239,
                    },
                },
            },
            'belt': {
                'ootb': {
                    'Sentinel_Belt_GrenadeT5': 7914,
                    'Sentinel_Belt_Claymore': 7421,
                },
                'other': {
                    'Sentinel_Belt_ArmoredClaymore': 8240,
                },
            },
            'packs': {
                'ootb': {
                },
                'other': {
                    'Sentinel_Pack_EnergyRecharge': 7900,
                    # 'Sentinel_Pack_DropJammer': 7456, # Repurposed as Drop Station
                },
            },
            'skins': {
                'ootb': {
                    'Skin SEN': 8327,
                    'Skin SEN Mercenary': 8337,
                },
                'other': {},
            }
        },
        'soldier': {
            'weapons': {
                'impact': {
                    'ootb': {
                        'Soldier_Primary_Spinfusor': 7401,
                        'Technician_Primary_Thumper': 7461,
                        'Soldier_Secondary_ThumperD_MKD': 8417,
                        'Soldier_Primary_Twinfusor': 8257,
                        'Soldier_Primary_Spinfusor_100X': 8697,
                        'Soldier_Primary_Honorfusor': 8768,
                    },
                    'other': {
                        'Soldier_Secondary_ThumperD': 7462,
                    },
                },
                'timed': {
                    'ootb': {
                        'Raider_Primary_ArxBuster': 7384,
                        'Raider_Primary_GrenadeLauncher': 7416,
                    },
                    'other': {
                        'Raider_Primary_ArxBuster_MKD': 8391,
                    },
                },
                'speciality': {
                    'ootb': {
                        'Technician_Secondary_RepairToolSD': 7436,
                        'Medium_ElfProjector': 8765,
                    },
                    'other': {
                        'Technician_Secondary_RepairToolSD_MKD': 8405,
                    },
                },
                'bullet': {
                    'ootb': {
                        'Soldier_Primary_AssaultRifle': 7385,
                        'Raider_Secondary_NJ4SMG': 7441,
                        'Raider_Secondary_NJ5SMG': 8249,
                        'Raider_Primary_PlasmaGun': 8251,
                        'Medium_Sidearm_NovaBlaster': 7394,
                        'Soldier_Secondary_Eagle': 7388,
                    },
                    'other': {
                        'Soldier_Primary_AssaultRifle_MKD': 8406,
                        'Raider_Secondary_NJ4SMG_MKD': 8408,
                        'Technician_Primary_TCN4': 7443,
                        'Technician_Primary_TCN4_MKD': 8410,
                    },
                },
                'short_range': {
                    'ootb': {
                        'Technician_Secondary_SawedOff': 7427,
                        'Technician_Primary_TC24': 8699, # Repurposed as Flak Cannon
                    },
                    'other': {},

                },
            },
            'belt': {
                'ootb': {
                    'Raider_Belt_EMPGrenade': 7444,
                    'Raider_Belt_WhiteOut': 7432,
                    'Raider_Belt_MIRVGrenade': 8247,
                    'Soldier_Belt_APGrenade': 7434,
                },
                'other': {
                    'Raider_Belt_EMPGrenade_MKD': 8395,
                    'Soldier_Belt_FragGrenadeXL': 7430,
                    'Soldier_Belt_FragGrenadeXL_MKD': 8399,
                    'Soldier_Belt_ProximityGrenade': 8222,
                },
            },
            'packs': {
                'ootb': {
                    'Raider_Pack_Shield': 7832,
                    'Raider_Pack_Jammer': 7827,
                    'Soldier_Pack_Utility': 8223,
                    'Technician_Pack_LightTurret': 7413,
                    'Technician_Pack_EXRTurret': 7417,
                    'Sentinel_Pack_DropJammer': 7456,  # Repurposed
                },
                'other': {
                    'Soldier_Pack_EnergyPool': 7824,
                },
            },
            'skins': {
                'ootb': {
                    'Skin SLD': 8328,
                    'Skin RDR': 8330,
                    'Skin TCN': 8329,
                    'Skin SLD Mercenary': 8748,
                    'Skin RDR Mercenary': 8352,
                    'Skin TCN Mercenary': 8731,
                    'Skin RDR Griever': 8351,
                },
                'other': {},

            }
        },
        'juggernaught': {
            'weapons': {
                'impact': {
                    'ootb': {
                        'Brute_Primary_HeavySpinfusor': 7448,
                        'Brute_Primary_HeavySpinfusor_MKD': 8414,
                        'Doombringer_Primary_HeavyBoltLauncher': 7452,
                        'Juggernaut_Secondary_HeavyTwinfusor': 8656,
                    },
                    'other': {
                        'Juggernaut_Secondary_SpinfusorD': 7446,
                        'Juggernaut_Secondary_SpinfusorD_MKD': 8413,
                    },
                },
                'timed': {
                    'ootb': {
                        'Juggernaut_Primary_FusionMortar': 7393,
                        'Juggernaut_Primary_MIRVLauncher': 7457,
                    },
                    'other': {
                        'Juggernaut_Primary_FusionMortar_MKD': 8400,
                    },
                },
                'speciality': {
                    'ootb': {
                        'Doombringer_Secondary_SaberLauncher': 7398,
                        'Brute_Primary_SpikeLauncher': 8401,
                    },
                    'other': {
                        'Doombringer_Secondary_SaberLauncher_MKD': 8357,
                    },
                },
                'bullet': {
                    'ootb': {
                        'Doombringer_Primary_ChainGun': 7386,
                        'Juggernaut_Secondary_X1LMG': 7458,
                        'Brute_Secondary_PlasmaCannon': 8250,
                        'Heavy_Sidearm_NovaBlaster_MKD': 8403,
                        'Brute_Secondary_NovaColt': 7431,
                    },
                    'other': {
                        'Doombringer_Primary_ChainGun_MKD': 8392,
                    },
                },
                'short_range': {
                    'ootb': {
                        'Brute_Secondary_AutoShotgun': 7449,
                        'Elf_FlakCannon': 8766,
                    },
                    'other': {
                        'Brute_Secondary_AutoShotgun_MKD': 8412,
                    },
                },
            },
            'belt': {
                'ootb': {
                    # <VERIFY> What is the JUG's OOTB grenade really? Neither FragXL or HeavyAP it seems
                    'Brute_Belt_FractalGrenade': 7428,
                    'Doombringer_Belt_Mine': 7392,
                },
                'other': {
                    'Juggernaut_Belt_HeavyAPGrenade': 7447,
                    'Juggernaut_Belt_HeavyAPGrenade_MKD': 8394,
                    'Brute_Belt_FractalGrenade_MKD': 8397,
                    'Brute_Belt_LightStickyGrenade': 7455,
                    'Juggernaut_Belt_DiskToss': 7459,
                },
            },
            'packs': {
                'ootb': {
                    'Brute_Pack_HeavyShield': 7826,
                    'Doombringer_Pack_ForceField': 7411,
                    'Brute_Pack_SurvivalPack': 8255,
                },
                'other': {
                    'Brute_Pack_MinorEnergy': 7830,
                },
            },
            'skins': {
                'ootb': {
                    'Skin JUG': 8331,
                    'Skin BRT': 8333,
                    'Skin DMB': 8332,
                    'Skin JUG Mercenary': 8745,
                    'Skin BRT Mercenary': 8663,
                    'Skin DMB Mercenary': 8744,
                },
                'other': {},
            }
        },
    },
    'voices': {
        'ootb': {
            'Voice Light': 8666,
            'Voice Medium': 8667,
            'Voice Heavy': 8668,
            'Voice Dark': 8669,
            'Voice Fem1': 8670,
            'Voice Fem2': 8671,
            'Voice Aus': 8695,
            'Voice T2 Fem01': 8712,
            'Voice T2 Fem02': 8714,
            'Voice T2 Fem03': 8715,
            'Voice T2 Fem04': 8716,
            'Voice T2 Fem05': 8717,
            'Voice T2 Male01': 8719,
            'Voice T2 Male02': 8720,
            'Voice T2 Male03': 8721,
            'Voice T2 Male04': 8722,
            'Voice T2 Male05': 8723,
            'Voice T2 Derm01': 8724,
            'Voice T2 Derm02': 8725,
            'Voice T2 Derm03': 8726,
            'Voice Total Biscuit': 8747,
            'Voice Stowaway': 8749,
        },
        'other': {
            'Voice Basement Champion': 8750,  # Unreleased voice
        },

    }
}

# Definition of items that should not appear in the menu at all
items_to_remove: Set[str] = set()

# Definition of items that should appear in the menu, but should be by default locked
items_to_lock: Set[str] = set()

# Processed form containing the information needed to build the menu content
class_menu_data: Unlockables = build_class_menu_data(game_classes, weapon_categories, hierarchical_definitions,
                                                     items_to_remove, items_to_lock, True, True)
