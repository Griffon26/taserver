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

from typing import NamedTuple, Dict, Set


class GameClass:

    def __init__(self, class_id: int, secondary_id: int, family_info_name: str, short_name: str):
        self.class_id = class_id
        self.secondary_id = secondary_id
        self.family_info_name = family_info_name
        self.short_name = short_name

    def __hash__(self):
        return self.class_id.__hash__()

    def __repr__(self):
        return f'GameClass({self.class_id}, {self.secondary_id}, "{self.family_info_name}", "{self.short_name}")'


class UnlockableItem:
    """
    An unlockable in-game item of any kind
    """

    def __init__(self, name: str, item_id: int, shown: bool = True, unlocked: bool = True) -> None:
        self.name = name
        self.item_id = item_id
        self.shown = shown
        self.unlocked = unlocked

    def __hash__(self):
        return self.item_id.__hash__()

    def __repr__(self):
        return f'UnlockableItem("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


class UnlockableClassSpecificItem(UnlockableItem):
    """
    An unlockable in-game item tied to a specific class
    """

    def __init__(self, name: str, item_id: int, class_id: int, shown: bool = True, unlocked: bool = True) -> None:
        super().__init__(name, item_id, shown, unlocked)
        self.class_id = class_id

    def __repr__(self):
        return f'UnlockableClassSpecificItem("{self.name}", {self.item_id}, ' \
               f'{self.class_id}, {self.shown}, {self.unlocked})'


class UnlockableWeapon(UnlockableClassSpecificItem):
    """
    An unlockable in-game weapon
    """

    def __init__(self, name: str, item_id: int, class_id: int,
                 category: int, shown: bool = True, unlocked: bool = True) -> None:
        super().__init__(name, item_id, class_id, shown, unlocked)
        self.category = category

    def __repr__(self):
        return f'UnlockableWeapon("{self.name}", {self.item_id}, ' \
               f'{self.class_id}, {self.category}, {self.shown}, {self.unlocked})'


class UnlockableVoice(UnlockableItem):

    def __repr__(self):
        return f'UnlockableVoice("{self.name}", {self.item_id}, {self.shown}, {self.unlocked})'


class ClassUnlockables(NamedTuple):
    """
    Definition of the intended state of a class in the loadout menus
    """
    weapons: Set[UnlockableWeapon]
    belt_items: Set[UnlockableClassSpecificItem]
    packs: Set[UnlockableClassSpecificItem]
    skins: Set[UnlockableClassSpecificItem]


class Unlockables(NamedTuple):
    """
    Definition of the intended state of the whole loadout menu
    """
    classes: Dict[str, GameClass]  # Valid in-game classes
    categories: Dict[str, Dict[str, int]]
    class_items: Dict[GameClass, ClassUnlockables]
    voices: Set[UnlockableVoice]


def process_class_items(game_class: GameClass, categories: Dict[str, Dict[str, int]], items_def: Dict,
                        removals: Set[str], locked: Set[str]) -> ClassUnlockables:

    # Weapons
    weapons = {UnlockableWeapon(item_name, item_id,
                                game_class.class_id, categories[game_class.short_name][category_name],
                                item_name not in removals, item_name not in locked)
               for category_name, category_def
               in items_def['weapons'].items()
               for item_name, item_id
               in category_def.items()}

    # Belt
    belt = {UnlockableClassSpecificItem(item_name, item_id, game_class.class_id,
                                        item_name not in removals, item_name not in locked)
            for item_name, item_id
            in items_def['belt'].items()}

    # Packs
    packs = {UnlockableClassSpecificItem(item_name, item_id, game_class.class_id,
                                         item_name not in removals, item_name not in locked)
             for item_name, item_id
             in items_def['packs'].items()}

    # Skins
    skins = {UnlockableClassSpecificItem(item_name, item_id, game_class.class_id,
                                         item_name not in removals, item_name not in locked)
             for item_name, item_id
             in items_def['skins'].items()}

    return ClassUnlockables(weapons, belt, packs, skins)


def build_class_menu_data(classes: Dict[str, GameClass],
                          categories: Dict[str, Dict[str, int]],
                          definitions: Dict,
                          removals: Set[str],
                          locked: Set[str]) -> Unlockables:
    voices = {UnlockableVoice(name, item_id, name not in removals, name not in locked)
              for name, item_id
              in definitions['voices'].items()}

    class_items = {game_class: process_class_items(game_class, categories,
                                                   definitions['classes'][class_name], removals, locked)
                   for class_name, game_class
                   in classes.items()}

    unlockables = Unlockables(classes, categories, class_items, voices)

    return unlockables


game_classes: Dict[str, GameClass] = {
    'light': GameClass(1683, 101330, 'TrFamilyInfo_Light_Pathfinder', 'light'),
    'medium': GameClass(1693, 101342, 'TrFamilyInfo_Medium_Soldier', 'medium'),
    'heavy': GameClass(1692, 101341, 'TrFamilyInfo_Heavy_Juggernaught', 'heavy'),
}

weapon_categories: Dict[str, Dict[str, int]] = {
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

# Definition of where items appear in the menu (including weapons going to be removed/locked)
# <VERIFY> Moving these should move where the item appears, e.g. which class/category it is
hierarchical_definitions = {
    'classes': {
        'light': {
            'weapons': {
                'impact': {
                    'Pathfinder_Primary_LightSpinfusor': 7422,
                    'Pathfinder_Primary_BoltLauncher': 7422,
                    'Pathfinder_Primary_LightSpinfusor_100X': 8696,
                    'Pathfinder_Primary_LightTwinfusor': 8245,
                    # GOTY
                    'Pathfinder_Primary_LightSpinfusor_MKD': 8415,
                    'Infiltrator_Primary_StealthLightSpinfusor': 7902,
                },
                'timed': {
                    'Light_Primary_LightGrenadeLauncher': 8761,
                    'Infiltrator_Primary_RemoteArxBuster': 8252,
                },
                'speciality': {
                    'Sentinel_Primary_SniperRifle': 7400,
                    'Sentinel_Primary_PhaseRifle': 7395,
                    # GOTY
                    'Sentinel_Primary_SniperRifle_MKD': 8407,
                    'Sentinel_Primary_SAP20': 8254,
                },
                'bullet': {
                    'Pathfinder_Secondary_LightAssaultRifle': 7438,
                    'Sentinel_Secondary_Falcon': 7419,
                    'Light_Sidearm_Sparrow': 7433,
                    'Infiltrator_Secondary_ThrowingKnives': 8256,
                    # GOTY
                    'Infiltrator_Primary_RhinoSMG': 7397,
                    'Infiltrator_Primary_RhinoSMG_MKD': 8409,
                    'Infiltrator_Secondary_SN7': 7418,
                    'Infiltrator_Secondary_SN7_MKD': 8404,
                },
                'short_range': {
                    'Pathfinder_Secondary_Shotgun': 7399,
                    'All_H1_Shocklance': 7435,
                    # GOTY
                    'Pathfinder_Secondary_Shotgun_MKD': 8411,
                    'Sentinel_Secondary_AccurizedShotgun': 8239,
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
                # GOTY
                'Pathfinder_Belt_ImpactNitron_MKD': 8396,
                'Infiltrator_Belt_StickyGrenade_MKD': 8398,
                'Sentinel_Belt_ArmoredClaymore': 8240,
            },
            'packs': {
                'Pathfinder_Pack_JumpPack': 7822,
                'Pathfinder_Pack_EnergyRecharge': 7825,
                'Infiltrator_Pack_Stealth': 7833,
                # GOTY
                'Sentinel_Pack_EnergyRecharge': 7900,
                # 'Sentinel_Pack_DropJammer': 7456, # Repurposed as Drop Station I think?
            },
            'skins': {
                'Skin PTH': 7834,
                'Skin INF': 7835,
                'Skin SEN': 8327,
                'Skin PTH Mercenary': 8326,
                'Skin INF Mercenary': 8336,
                'Skin SEN Mercenary': 8337,
                'Skin INF Assassin': 8665,
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
                    'Soldier_Primary_Honorfusor': 8768,
                    # GOTY
                    'Soldier_Secondary_ThumperD': 7462,
                },
                'timed': {
                    'Raider_Primary_ArxBuster': 7384,
                    'Raider_Primary_GrenadeLauncher': 7416,
                    # GOTY
                    'Raider_Primary_ArxBuster_MKD': 8391,
                },
                'speciality': {
                    'Technician_Secondary_RepairToolSD': 7436,
                    'Medium_ElfProjector': 8765,
                    # GOTY
                    'Technician_Secondary_RepairToolSD_MKD': 8405,
                },
                'bullet': {
                    'Soldier_Primary_AssaultRifle': 7385,
                    'Raider_Secondary_NJ4SMG': 7441,
                    'Raider_Secondary_NJ5SMG': 8249,
                    'Raider_Primary_PlasmaGun': 8251,
                    'Medium_Sidearm_NovaBlaster': 7394,
                    'Soldier_Secondary_Eagle': 7388,
                    # GOTY
                    'Soldier_Primary_AssaultRifle_MKD': 8406,
                    'Raider_Secondary_NJ4SMG_MKD': 8408,
                    'Technician_Primary_TCN4': 7443,
                    'Technician_Primary_TCN4_MKD': 8410,
                },
                'short_range': {
                    'Technician_Secondary_SawedOff': 7427,
                    'Technician_Primary_TC24': 8699,
                },
            },
            'belt': {
                'Raider_Belt_EMPGrenade': 7444,
                'Raider_Belt_WhiteOut': 7432,
                'Raider_Belt_MIRVGrenade': 8247,
                'Soldier_Belt_APGrenade': 7434,
                # GOTY
                'Raider_Belt_EMPGrenade_MKD': 8395,
                'Soldier_Belt_FragGrenadeXL': 7430,
                'Soldier_Belt_FragGrenadeXL_MKD': 8399,
                'Soldier_Belt_ProximityGrenade': 8222,
            },
            'packs': {
                'Raider_Pack_Shield': 7832,
                'Raider_Pack_Jammer': 7827,
                'Soldier_Pack_Utility': 8223,
                'Technician_Pack_LightTurret': 7413,
                'Technician_Pack_EXRTurret': 7417,
                'Sentinel_Pack_DropJammer': 7456,  # Repurposed
                # GOTY
                'Soldier_Pack_EnergyPool': 7824,
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
                    # GOTY
                    'Juggernaut_Secondary_SpinfusorD': 7446,
                    'Juggernaut_Secondary_SpinfusorD_MKD': 8413,
                },
                'timed': {
                    'Juggernaut_Primary_FusionMortar': 7393,
                    'Juggernaut_Primary_MIRVLauncher': 7457,
                    # GOTY
                    'Juggernaut_Primary_FusionMortar_MKD': 8400,
                },
                'speciality': {
                    'Doombringer_Secondary_SaberLauncher': 7398,
                    'Brute_Primary_SpikeLauncher': 8401,
                    # GOTY
                    'Doombringer_Secondary_SaberLauncher_MKD': 8357,
                },
                'bullet': {
                    'Doombringer_Primary_ChainGun': 7386,
                    'Juggernaut_Secondary_X1LMG': 7458,
                    'Brute_Secondary_PlasmaCannon': 8250,
                    'Heavy_Sidearm_NovaBlaster_MKD': 8403,
                    'Brute_Secondary_NovaColt': 7431,
                    # GOTY
                    'Doombringer_Primary_ChainGun_MKD': 8392,
                },
                'short_range': {
                    'Brute_Secondary_AutoShotgun': 7449,
                    'Elf_FlakCannon': 8766,
                    # GOTY
                    'Brute_Secondary_AutoShotgun_MKD': 8412,
                },
            },
            'belt': {
                # <VERIFY> What is the JUG's OOTB grenade really? FragXL or HeavyAP?
                'Brute_Belt_FractalGrenade': 7428,
                'Doombringer_Belt_Mine': 7392,
                # GOTY
                'Juggernaut_Belt_HeavyAPGrenade': 7447,
                'Juggernaut_Belt_HeavyAPGrenade_MKD': 8394,
                'Brute_Belt_FractalGrenade_MKD': 8397,
                'Brute_Belt_LightStickyGrenade': 7455,
                'Juggernaut_Belt_DiskToss': 7459,
            },
            'packs': {
                'Brute_Pack_HeavyShield': 7826,
                'Doombringer_Pack_ForceField': 7411,
                'Brute_Pack_SurvivalPack': 8255,
                # GOTY
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
        'Voice Basement Champion': 8750,  # Unreleased voice?
    }
}

# Definition of items that should not appear in the menu at all
items_to_remove = {
    'Raider_Primary_GrenadeLauncher',
    'Raider_Belt_WhiteOut',
}

# Definition of items that should appear in the menu, but should be by default locked
items_to_lock = {
    'Soldier_Primary_Twinfusor',
    'Juggernaut_Secondary_HeavyTwinfusor',
    'Brute_Belt_FractalGrenade',
}

# Processed form containing the information needed to build the menu content
class_menu_data = build_class_menu_data(game_classes, weapon_categories, hierarchical_definitions,
                                        items_to_remove, items_to_lock)
