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

from typing import NamedTuple, Dict, Set, List, Tuple, Generator
from collections import OrderedDict
import copy
import itertools


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
                 short_name: str, purchase_name: str):
        self.class_id = class_id
        self.secondary_id = secondary_id
        self.family_info_name = family_info_name
        self.short_name = short_name
        self.purchase_name = purchase_name

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

    def __init__(self, name: str, item_id: int, shown: bool = True, unlocked: bool = True) -> None:
        super().__init__(name, item_id, shown)
        self.unlocked = unlocked

    def __hash__(self):
        return self.item_id.__hash__()

    def __repr__(self):
        return f'UnlockableItem("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


class UnlockableClassSpecificItem(UnlockableItem):
    """
    An unlockable in-game item tied to a specific class
    """

    item_kind_id = 0x00D9

    def __init__(self, name: str, item_id: int, game_class: GameClass, shown: bool = True,
                 unlocked: bool = True) -> None:
        super().__init__(name, item_id, shown, unlocked)
        self.game_class = game_class

    def __repr__(self):
        return f'UnlockableClassSpecificItem("{self.name}", {self.item_id}, ' \
            f'{self.game_class.class_id}, {self.shown}, {self.unlocked})'


class UnlockableWeapon(UnlockableClassSpecificItem):
    """
    An unlockable in-game weapon
    """

    def __init__(self, name: str, item_id: int, game_class: GameClass,
                 category: int, shown: bool = True, unlocked: bool = True) -> None:
        super().__init__(name, item_id, game_class, shown, unlocked)
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


class UnlockablePerk(UnlockableItem):
    """
    An unlockable in-game perk, not specific to a class
    """
    item_kind_id = 0x27F5

    def __repr__(self):
        return f'UnlockablePerk("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


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
    perks: List[UnlockablePerk]
    voices: List[UnlockableVoice]

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
        items.extend(self.perks)
        items.extend(self.voices)
        return items


def process_class_items(game_class: GameClass, categories: Dict[str, Dict[str, int]], items_def: Dict,
                        removals: Set[str], locked: Set[str]) -> ClassUnlockables:
    """
    Process a hierarchical definition of a class's items into a ClassUnlockables structure

    :param game_class: the game class
    :param categories: mapping of classes to the mappings of categories of weapons for each class
    :param items_def: hierarchical items definition
    :param removals: list of item names to remove (not show at all in the menu)
    :param locked: list of item names to show locked in the menu
    :return: the resulting ClassUnlockables
    """
    # Weapons
    weapons = [UnlockableWeapon(item_name, item_id,
                                game_class, categories[game_class.short_name][category_name],
                                item_name not in removals,
                                item_name not in locked)
               for category_name, category_def
               in items_def['weapons'].items()
               for item_name, item_id
               in category_def.items()]

    # Belt
    belt = [UnlockableClassSpecificItem(item_name, item_id, game_class,
                                        item_name not in removals,
                                        item_name not in locked)
            for item_name, item_id
            in items_def['belt'].items()]

    # Packs
    packs = [UnlockablePack(item_name, item_id, game_class,
                            item_name not in removals,
                            item_name not in locked)
             for item_name, item_id
             in items_def['packs'].items()]

    # Skins
    skins = [UnlockableSkin(item_name, item_id, game_class,
                            item_name not in removals,
                            item_name not in locked)
             for item_name, item_id
             in items_def['skins'].items()]

    return ClassUnlockables(weapons, belt, packs, skins)


def build_class_menu_data(classes: Dict[str, GameClass],
                          categories: Dict[str, Dict[str, int]],
                          definitions: Dict,
                          removals: Set[str],
                          locked: Set[str]) -> Unlockables:
    """
    Process a full hierarchical definition of the item menus into a structured Unlockables object

    :param classes: mapping of game class names to GameClass definitions
    :param categories: mapping of class names to the mappings of categories of weapons for each class
    :param definitions: the original hierarchical definition of the menus
    :param removals: list of item names to remove (not show at all in the menu)
    :param locked: list of item names to show locked in the menu
    :return: the resulting Unlockables object
    """
    enabled_classes = classes

    class_purchases = {UnlockableGameClass(game_class)
                       for name, game_class
                       in enabled_classes.items()}

    perks = [UnlockablePerk(name, item_id,
                            name not in removals, name not in locked)
             for name, item_id
             in dict(definitions['perkA'], **definitions['perkB']).items()]

    voices = [UnlockableVoice(name, item_id,
                              name not in removals, name not in locked)
              for name, item_id
              in definitions['voices'].items()]

    class_items = {game_class: process_class_items(game_class, categories,
                                                   definitions['classes'][class_name],
                                                   removals, locked)
                   for class_name, game_class
                   in enabled_classes.items()}

    unlockables = Unlockables(enabled_classes, class_purchases, categories, class_items, perks, voices)

    return unlockables


# Definition of the game class info; the class name keys should match weapon_categories and hierarchical_definitions
game_classes: Dict[str, GameClass] = {
    'light': GameClass(1683, 101330, 'TrFamilyInfo_Light_Pathfinder', 'light', "Pathfinder Purchase"),
    'medium': GameClass(1693, 101342, 'TrFamilyInfo_Medium_Soldier', 'medium', "Soldier Purchase"),
    'heavy': GameClass(1692, 101341, 'TrFamilyInfo_Heavy_Juggernaught', 'heavy', "Juggernaught Purchase"),
}

# Definition of the weapon categories; category names should match hierarchical_definitions
_weapon_categories_ootb: Dict[str, Dict[str, int]] = {
    'light': {
        'impact': 11126,
        'timed': 11142,
        'speciality': 11128,
        'bullet': 11127,
        'short_range': 11129
    },
    'medium': {
        'impact': 11131,
        'timed': 11133,
        'speciality': 11135,
        'bullet': 11132,
        'short_range': 11143
    },
    'heavy': {
        'impact': 11136,
        'timed': 11139,
        'speciality': 11141,
        'bullet': 11137,
        'short_range': 11138
    },
}
# Definition of the weapon categories; category names should match hierarchical_definitions
_weapon_categories_goty: Dict[str, Dict[str, int]] = {
    'light': {
        'impact': 11126,
        'timed': 11142,
        'speciality': 11128,  # Dummy tertiary
        'bullet': 11127,  # Used for perks
    },
    'medium': {
        'impact': 11131,
        'timed': 11133,
        'speciality': 11135,  # Dummy tertiary
        'bullet': 11132,  # Used for perks
    },
    'heavy': {
        'impact': 11136,
        'timed': 11139,
        'speciality': 11141,  # Dummy tertiary
        'bullet': 11137,  # Used for perks
    },
}

# Definition of where items appear in the menu (including weapons going to be removed/locked)
# Moving items will change where the item appears in the menus, e.g. which class/category it is available to
_hierarchical_definitions_ootb = {
    'classes': {
        'light': {
            'weapons': {
                'impact': {
                    'Pathfinder_Primary_LightSpinfusor': 7422,
                    'Pathfinder_Primary_BoltLauncher': 7425,
                    'Pathfinder_Primary_LightSpinfusor_100X': 8696,
                    'Pathfinder_Primary_LightTwinfusor': 8245,
                },
                'timed': {
                    'Light_Primary_LightGrenadeLauncher': 8761,
                    'Infiltrator_Primary_RemoteArxBuster': 8252,
                },
                'speciality': {
                    'Sentinel_Primary_SniperRifle': 7400,
                    'Sentinel_Primary_PhaseRifle': 7395,
                },
                'bullet': {
                    'Pathfinder_Secondary_LightAssaultRifle': 7438,
                    'Sentinel_Secondary_Falcon': 7419,
                    'Light_Sidearm_Sparrow': 7433,
                    'Infiltrator_Secondary_ThrowingKnives': 8256,
                },
                'short_range': {
                    'Pathfinder_Secondary_Shotgun': 7399,
                    'All_H1_Shocklance': 7435,
                },
            },
            'belt': {
                'Pathfinder_Belt_ImpactNitron': 7387,
                'Pathfinder_Belt_STGrenade': 7437,
                'Sentinel_Belt_GrenadeT5': 7914,
                'Infiltrator_Belt_StickyGrenade': 7402,
                'Sentinel_Belt_Claymore': 7421,
                'Infiltrator_Belt_PrismMines': 7440,
                'Infiltrator_Belt_NinjaSmoke': 8248,
            },
            'packs': {
                'Pathfinder_Pack_JumpPack': 7822,
                'Pathfinder_Pack_EnergyRecharge': 7825,
                'Infiltrator_Pack_Stealth': 7833,
                'Sentinel_Pack_EnergyRecharge': 7900,
            },
            'skins': {
                'Skin PTH': 7834,
                'Skin INF': 7835,
                'Skin SEN': 8327,
                'Skin PTH Mercenary': 8326,
                'Skin INF Mercenary': 8336,
                'Skin INF Assassin': 8337,
                'Skin SEN Mercenary': 8665,
            }
        },
        'medium': {
            'weapons': {
                'impact': {
                    'Soldier_Primary_Spinfusor': 7401,
                    'Technician_Primary_Thumper': 7461,
                    'Soldier_Secondary_ThumperD_MKD': 8417,
                    'Soldier_Primary_Twinfusor': 8257,
                    'Soldier_Primary_Spinfusor_100X': 8697,
                },
                'timed': {
                    'Raider_Primary_ArxBuster': 7384,
                    'Raider_Primary_GrenadeLauncher': 7416,
                },
                'speciality': {
                    'Technician_Secondary_RepairToolSD': 7436,
                    'Medium_ElfProjector': 8765,
                    'Soldier_Primary_Honorfusor': 8768,
                },
                'bullet': {
                    'Soldier_Primary_AssaultRifle': 7385,
                    'Raider_Secondary_NJ4SMG': 7441,
                    'Raider_Secondary_NJ5SMG': 8249,
                    'Raider_Primary_PlasmaGun': 8251,
                    'Medium_Sidearm_NovaBlaster': 7394,
                    'Soldier_Secondary_Eagle': 7388,
                },
                'short_range': {
                    'Technician_Secondary_SawedOff': 7427,
                    'Technician_Primary_TC24': 8699,  # Repurposed as Flak Cannon
                },
            },
            'belt': {
                'Raider_Belt_EMPGrenade': 7444,
                'Raider_Belt_WhiteOut': 7432,
                'Raider_Belt_MIRVGrenade': 8247,
                'Soldier_Belt_APGrenade': 7434,
                'Technician_Belt_MotionAlarm': 7426,
            },
            'packs': {
                'Raider_Pack_Shield': 7832,
                'Raider_Pack_Jammer': 7827,
                'Soldier_Pack_Utility': 8223,
                'Technician_Pack_LightTurret': 7413,
                'Technician_Pack_EXRTurret': 7417,
                'Sentinel_Pack_DropJammer': 7456,  # Repurposed
            },
            'skins': {
                'Skin SLD': 8328,
                'Skin RDR': 8330,
                'Skin TCN': 8329,
                'Skin SLD Mercenary': 8748,
                'Skin RDR Mercenary': 8352,
                'Skin TCN Mercenary': 8731,
                'Skin RDR Griever': 8351,
            }
        },
        'heavy': {
            'weapons': {
                'impact': {
                    'Brute_Primary_HeavySpinfusor': 7448,
                    'Brute_Primary_HeavySpinfusor_MKD': 8414,
                    'Doombringer_Primary_HeavyBoltLauncher': 7452,
                    'Juggernaut_Secondary_HeavyTwinfusor': 8656,
                },
                'timed': {
                    'Juggernaut_Primary_FusionMortar': 7393,
                    'Juggernaut_Primary_MIRVLauncher': 7457,
                },
                'speciality': {
                    'Doombringer_Secondary_SaberLauncher': 7398,
                    'Brute_Primary_SpikeLauncher': 8357,
                },
                'bullet': {
                    'Doombringer_Primary_ChainGun': 7386,
                    'Juggernaut_Secondary_X1LMG': 7458,
                    'Brute_Secondary_PlasmaCannon': 8250,
                    'Heavy_Sidearm_NovaBlaster_MKD': 8403,
                    'Brute_Secondary_NovaColt': 7431,
                },
                'short_range': {
                    'Brute_Secondary_AutoShotgun': 7449,
                    'Elf_FlakCannon': 8766,
                },
            },
            'belt': {
                'Doombringer_Belt_FragGrenade': 7390,
                'Brute_Belt_FractalGrenade': 7428,
                'Doombringer_Belt_Mine': 7392,
            },
            'packs': {
                'Brute_Pack_HeavyShield': 7826,
                'Doombringer_Pack_ForceField': 7411,
                'Brute_Pack_SurvivalPack': 8255,
                'Brute_Pack_MinorEnergy': 7830,
            },
            'skins': {
                'Skin JUG': 8331,
                'Skin BRT': 8333,
                'Skin DMB': 8332,
                'Skin JUG Mercenary': 8745,
                'Skin BRT Mercenary': 8663,
                'Skin DMB Mercenary': 8744,
            }
        },
    },
    'perkA': {
        'Perk Safe Fall': 8162,
        'Perk Safety Third': 8163,
        'Perk Reach': 7916,
        'Perk Wheel Deal': 8169,
        'Perk Bounty Hunter': 8153,
        'Perk Close Combat': 8156,
        'Perk Stealthy': 8164,
        'Perk Super Capacitor': 8165,
        'Perk Looter': 8158,
        'Perk Rage': 8232,
    },
    'perkB': {
        'Perk Survivalist': 8167,
        'Perk Egocentric': 7917,
        'Perk Pilot': 8159,
        'Perk Super Heavy': 8166,
        'Perk Ultra Capacitor': 8168,
        'Perk Quickdraw': 8161,
        'Perk Mechanic': 8170,
        'Perk Determination': 8157,
        'Perk Potential Energy': 8160,
        'Perk Sonic Punch': 8231,
        'Perk Lightweight': 8646,
    },
    'voices': {
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
        'Voice Basement Champion': 8750,  # Unreleased voice
    }
}

_hierarchical_definitions_goty = {
    'classes': {
        'pth': {
            'weapons': {
                'primary': {
                    'Pathfinder_Primary_LightSpinfusor': 7422,
                    'Pathfinder_Primary_BoltLauncher': 7425,
                    'Pathfinder_Primary_LightSpinfusor_100X': 8696,
                    'Pathfinder_Primary_LightTwinfusor': 8245,
                    'Pathfinder_Primary_LightSpinfusor_MKD': 8415,
                },
                'secondary': {
                    'Pathfinder_Secondary_LightAssaultRifle': 7438,
                    'Pathfinder_Secondary_Shotgun': 7399,
                    'Pathfinder_Secondary_Shotgun_MKD': 8411,
                    'All_H1_Shocklance': 7435,
                    # 'Light_Primary_LightGrenadeLauncher': 8761,  # OOTB only
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Pathfinder_Belt_ImpactNitron': 7387,
                'Pathfinder_Belt_STGrenade': 7437,
                'Pathfinder_Belt_ImpactNitron_MKD': 8396,
            },
            'packs': {
                'Pathfinder_Pack_JumpPack': 7822,
                'Pathfinder_Pack_EnergyRecharge': 7825,
            },
            'skins': {
                'Skin PTH': 7834,
                'Skin PTH Mercenary': 8326,
            },
        },
        'sen': {
            'weapons': {
                'primary': {
                    'Sentinel_Primary_SniperRifle': 7400,
                    'Sentinel_Primary_PhaseRifle': 7395,
                    'Sentinel_Primary_SniperRifle_MKD': 8407,
                    'Sentinel_Primary_SAP20': 8254,
                },
                'secondary': {
                    'Sentinel_Secondary_Falcon': 7419,
                    'Medium_Sidearm_NovaBlaster': 7394,
                    'Heavy_Sidearm_NovaBlaster_MKD': 8403,
                    'Sentinel_Secondary_AccurizedShotgun': 8239,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Sentinel_Belt_GrenadeT5': 7914,
                'Sentinel_Belt_Claymore': 7421,
                'Sentinel_Belt_ArmoredClaymore': 8240,
            },
            'packs': {
                'Pathfinder_Pack_EnergyRecharge': 7825,
                # 'Sentinel_Pack_EnergyRecharge': 7900, # Repurposed as light utility pack
                # 'Sentinel_Pack_DropJammer': 7456, # Repurposed as Drop Station
            },
            'skins': {
                'Skin SEN': 8327,
                'Skin SEN Mercenary': 8665,
            },
        },
        'inf': {
            'weapons': {
                'primary': {
                    'Infiltrator_Primary_StealthLightSpinfusor': 7902,
                    'Infiltrator_Primary_RemoteArxBuster': 8252,
                    'Infiltrator_Primary_RhinoSMG': 7397,
                    'Infiltrator_Primary_RhinoSMG_MKD': 8409,
                },
                'secondary': {
                    'Infiltrator_Secondary_SN7': 7418,
                    'Infiltrator_Secondary_SN7_MKD': 8404,
                    'Infiltrator_Secondary_ThrowingKnives': 8256,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Infiltrator_Belt_StickyGrenade': 7402,
                'Infiltrator_Belt_StickyGrenade_MKD': 8398,
                'Infiltrator_Belt_PrismMines': 7440,
                # 'Infiltrator_Belt_NinjaSmoke': 8248, # Repurposed as chaff grenades
            },
            'packs': {
                'Pathfinder_Pack_EnergyRecharge': 7825,
                'Infiltrator_Pack_Stealth': 7833,
                # 'Sentinel_Pack_EnergyRecharge': 7900, # Repurposed as light utility pack
                # 'Sentinel_Pack_DropJammer': 7456, # Repurposed as Drop Station
            },
            'skins': {
                'Skin INF': 7835,
                'Skin INF Mercenary': 8336,
                'Skin INF Assassin': 8337,
            },
        },
        'sld': {
            'weapons': {
                'primary': {
                    'Soldier_Primary_Spinfusor': 7401,
                    'Soldier_Primary_Twinfusor': 8257,
                    'Soldier_Primary_Honorfusor': 8768,
                    'Soldier_Primary_AssaultRifle': 7385,
                    'Soldier_Primary_AssaultRifle_MKD': 8406,
                },
                'secondary': {
                    'Soldier_Secondary_SpareSpinfusor': 8697,
                    'Soldier_Secondary_ThumperD': 7462,
                    'Soldier_Secondary_ThumperD_MKD': 8417,
                    'Soldier_Secondary_Eagle': 7388,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Soldier_Belt_FragGrenadeXL': 7430,
                'Soldier_Belt_FragGrenadeXL_MKD': 8399,
                'Soldier_Belt_APGrenade': 7434,
                'Soldier_Belt_ProximityGrenade': 8222,
            },
            'packs': {
                'Soldier_Pack_EnergyPool': 7824,
                'Soldier_Pack_Utility': 8223,
            },
            'skins': {
                'Skin SLD': 8328,
                'Skin SLD Mercenary': 8748,
            },
        },
        'rdr': {
            'weapons': {
                'primary': {
                    'Raider_Primary_ArxBuster': 7384,
                    'Raider_Primary_ArxBuster_MKD': 8391,
                    'Raider_Primary_GrenadeLauncher': 7416,
                    'Raider_Primary_PlasmaGun': 8251,
                },
                'secondary': {
                    'Raider_Secondary_NJ4SMG': 7441,
                    'Raider_Secondary_NJ4SMG_MKD': 8408,
                    'Raider_Secondary_NJ5SMG': 8249,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Raider_Belt_EMPGrenade': 7444,
                'Raider_Belt_WhiteOut': 7432,
                'Raider_Belt_MIRVGrenade': 8247,
                'Raider_Belt_EMPGrenade_MKD': 8395,
            },
            'packs': {
                'Raider_Pack_Shield': 7832,
                'Raider_Pack_Jammer': 7827,
            },
            'skins': {
                'Skin RDR': 8330,
                'Skin RDR Mercenary': 8352,
                'Skin RDR Griever': 8351,
            },
        },
        'tcn': {
            'weapons': {
                'primary': {
                    'Technician_Primary_Thumper': 7461,
                    'Technician_Primary_TCN4': 7443,
                    'Technician_Primary_TCN4_MKD': 8410,
                    # 'Technician_Primary_TC24': 8699,  # Repurposed as Flak Cannon
                },
                'secondary': {
                    'Technician_Secondary_RepairToolSD': 7436,
                    # 'Technician_Secondary_RepairToolSD_MKD': 8405,  # Disabled, used as a placeholder tertiary
                    'Technician_Secondary_SawedOff': 7427,
                    'Light_Sidearm_Sparrow': 7433,
                    # 'Medium_ElfProjector': 8765, # OOTB only
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Technician_Belt_TCNG': 7736,
                'Technician_Belt_TCNG_MKD': 8416,
                'Technician_Belt_MotionAlarm': 7426,
                'Technician_Belt_RepairKit': 8698,
            },
            'packs': {
                # 'Sentinel_Pack_DropJammer': 7456,  # Repurposed as lunchbox
                'Technician_Pack_LightTurret': 7413,
                'Technician_Pack_EXRTurret': 7417,
            },
            'skins': {
                'Skin TCN': 8329,
                'Skin TCN Mercenary': 8731,
            },
        },
        'jug': {
            'weapons': {
                'primary': {
                    'Juggernaut_Primary_FusionMortar': 7393,
                    'Juggernaut_Primary_FusionMortar_MKD': 8400,
                    'Juggernaut_Primary_MIRVLauncher': 7457,
                },
                'secondary': {
                    'Juggernaut_Secondary_SpinfusorD': 7446,
                    'Juggernaut_Secondary_SpinfusorD_MKD': 8413,
                    'Juggernaut_Secondary_HeavyTwinfusor': 8656,
                    'Juggernaut_Secondary_X1LMG': 7458,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Juggernaut_Belt_HeavyAPGrenade': 7447,
                'Juggernaut_Belt_HeavyAPGrenade_MKD': 8394,
                'Juggernaut_Belt_DiskToss': 7459,
            },
            'packs': {
                'Juggernaut_Pack_HealthRegen': 7831,
                # 'Juggernaut_Pack_Energy': 7901,
            },
            'skins': {
                'Skin JUG': 8331,
                'Skin JUG Mercenary': 8745,
            },
        },
        'dmb': {
            'weapons': {
                'primary': {
                    'Doombringer_Primary_ChainGun': 7386,
                    'Doombringer_Primary_ChainGun_MKD': 8392,
                    'Doombringer_Primary_HeavyBoltLauncher': 7452,
                },
                'secondary': {
                    'Doombringer_Secondary_SaberLauncher': 7398,
                    'Doombringer_Secondary_SaberLauncher_MKD': 8401,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Doombringer_Belt_Mine': 7392,
                'Doombringer_Belt_FragGrenade': 7390,
            },
            'packs': {
                'Doombringer_Pack_ForceField': 7411,
            },
            'skins': {
                'Skin DMB': 8332,
                'Skin DMB Mercenary': 8744,
            },
        },
        'brt': {
            'weapons': {
                'primary': {
                    'Brute_Primary_HeavySpinfusor': 7448,
                    'Brute_Primary_HeavySpinfusor_MKD': 8414,
                    'Brute_Primary_SpikeLauncher': 8357,
                },
                'secondary': {
                    'Brute_Secondary_AutoShotgun': 7449,
                    'Brute_Secondary_AutoShotgun_MKD': 8412,
                    'Brute_Secondary_NovaColt': 7431,
                    'Brute_Secondary_PlasmaCannon': 8250,
                    # 'Elf_FlakCannon': 8766,
                    'All_H1_Shocklance': 7435,
                },
                'dummy': {
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                }
            },
            'belt': {
                'Brute_Belt_FractalGrenade': 7428,
                'Brute_Belt_FractalGrenade_MKD': 8397,
                'Brute_Belt_LightStickyGrenade': 7455,
            },
            'packs': {
                'Brute_Pack_HeavyShield': 7826,
                'Brute_Pack_MinorEnergy': 7830,
                'Brute_Pack_SurvivalPack': 8255,
            },
            'skins': {
                'Skin BRT': 8333,
                'Skin BRT Mercenary': 8663,
            },
        },
    },
    'perkA': {
        'Perk Safe Fall': 8162,
        'Perk Safety Third': 8163,
        'Perk Reach': 7916,
        'Perk Wheel Deal': 8169,
        'Perk Bounty Hunter': 8153,
        'Perk Close Combat': 8156,
        'Perk Stealthy': 8164,
        'Perk Super Capacitor': 8165,
        'Perk Looter': 8158,
        'Perk Rage': 8232,
    },
    'perkB': {
        'Perk Survivalist': 8167,
        'Perk Egocentric': 7917,
        'Perk Pilot': 8159,
        'Perk Super Heavy': 8166,
        'Perk Ultra Capacitor': 8168,
        'Perk Quickdraw': 8161,
        'Perk Mechanic': 8170,
        'Perk Determination': 8157,
        'Perk Potential Energy': 8160,
        'Perk Sonic Punch': 8231,
        'Perk Lightweight': 8646,
    },
    'voices': {
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
        'Voice Basement Champion': 8750,  # Unreleased voice

    }
}


def merge_goty_classes_for_non_modded_menus(goty_defs: Dict) -> Dict:
    result = dict()

    result['perkA'] = goty_defs['perkA'].copy()
    result['perkB'] = goty_defs['perkB'].copy()
    result['voices'] = goty_defs['voices'].copy()

    mappings = {
        'light': ['pth', 'sen', 'inf'],
        'medium': ['sld', 'rdr', 'tcn'],
        'heavy': ['jug', 'dmb', 'brt'],
    }

    category_mappings = {
        'primary': 'impact',
        'secondary': 'timed',
        'dummy': 'speciality',
    }

    result['classes'] = dict()

    for ootb_class, goty_classes in mappings.items():
        result['classes'][ootb_class] = dict()
        result['classes'][ootb_class]['weapons'] = dict()
        for goty_category, ootb_category in category_mappings.items():
            result['classes'][ootb_class]['weapons'][ootb_category] = dict()
            for goty_class in goty_classes:
                result['classes'][ootb_class]['weapons'][ootb_category] \
                    .update(goty_defs['classes'][goty_class]['weapons'].get(goty_category, dict()))
        for non_weapon_item_kind in ['belt', 'packs', 'skins']:
            result['classes'][ootb_class][non_weapon_item_kind] = dict()
            for goty_class in goty_classes:
                result['classes'][ootb_class][non_weapon_item_kind] \
                    .update(goty_defs['classes'][goty_class].get(non_weapon_item_kind, dict()))

    # In GOTY mode, add all encoded perk combinations as "bullet" weapons
    for c in game_classes.keys():
        result['classes'][c]['weapons']['bullet'] = {
            str(_encode_perks(perk_a, perk_b)): _encode_perks(perk_a, perk_b)
            for (perk_a, perk_b)
            in list(itertools.product(*[result['perkA'].values(),
                                        result['perkB'].values()]))
        }

    return result


def generate_class_menu_data_modded_defs(class_defs: Dict) -> List[Dict]:
    result = list()
    for kind in ['perkA', 'perkB', 'voices']:
        result.extend(({'id': item, 'kind': kind} for item in class_defs[kind].values()))

    for game_class_name, game_class_defs in class_defs['classes'].items():
        for weapon_category_name, weapon_category_defs in class_defs['classes'][game_class_name]['weapons'].items():
            result.extend(({
                'id': item,
                'kind': 'weapon',
                'cat': weapon_category_name,
                'class': game_class_name
            } for item in weapon_category_defs.values()))
        for kind in ['belt', 'packs', 'skins']:
            result.extend(({
                'id': item,
                'kind': kind,
                'class': game_class_name
            } for item in class_defs['classes'][game_class_name][kind].values()))

    return result


def _encode_perks(perk_a: int, perk_b: int):
    return (perk_a << 16) | perk_b


# Definition of items that should not appear in the menu at all
_items_to_remove: Set[str] = set()

# Definition of items that should appear in the menu, but should be by default locked
_items_to_lock: Set[str] = set()

# The game setting mode that should be used for all non-modded clients
UNMODDED_GAME_SETTING_MODE = 'ootb'

_built_class_menu_data = OrderedDict({
    UNMODDED_GAME_SETTING_MODE: build_class_menu_data(game_classes, _weapon_categories_ootb,
                                                      _hierarchical_definitions_ootb, _items_to_remove, _items_to_lock),
    'goty': build_class_menu_data(game_classes, _weapon_categories_goty,
                                  merge_goty_classes_for_non_modded_menus(_hierarchical_definitions_goty),
                                  _items_to_remove, _items_to_lock)
})

_class_menu_data_modded_defs = OrderedDict({
    UNMODDED_GAME_SETTING_MODE: generate_class_menu_data_modded_defs(_hierarchical_definitions_ootb),
    'goty': generate_class_menu_data_modded_defs(_hierarchical_definitions_goty)
})


def get_game_setting_modes():
    return _built_class_menu_data.keys()


def get_unmodded_class_menu_data() -> Unlockables:
    return _built_class_menu_data[UNMODDED_GAME_SETTING_MODE]


def get_class_menu_data_modded_defs(game_setting_mode: str) -> List[Dict]:
    return _class_menu_data_modded_defs[game_setting_mode]
