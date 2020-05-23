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

from bitarray import bitarray
from itertools import zip_longest
import struct

known_int_values = {
    203001: 'CONST_STAT_ACO_KS_FIVE',
    203002: 'CONST_STAT_ACO_KS_TEN',
    203003: 'CONST_STAT_ACO_KS_FIFTEEN',
    203004: 'CONST_STAT_ACO_KS_TWENTY',
    203005: 'CONST_STAT_ACO_KS_TWENTYFIVE',
    203006: 'CONST_STAT_ACO_KS_FIVE_SNIPING',
    203007: 'CONST_STAT_ACO_KS_TEN_SNIPING',
    203008: 'CONST_STAT_ACO_KS_FIFTEEN_SNIPING',
    203009: 'CONST_STAT_ACO_KS_FIVE_EXPLOSIVE',
    203010: 'CONST_STAT_ACO_KS_TEN_EXPLOSIVE',
    203011: 'CONST_STAT_ACO_KS_FIFTEEN_EXPLOSIVE',
    203012: 'CONST_STAT_ACO_KS_FIVE_SPINFUSOR',
    203013: 'CONST_STAT_ACO_KS_TEN_SPINFUSOR',
    203014: 'CONST_STAT_ACO_KS_FIFTEEN_SPINFUSOR',
    203015: 'CONST_STAT_ACO_MK_DOUBLE',
    203016: 'CONST_STAT_ACO_MK_TRIPLE',
    203017: 'CONST_STAT_ACO_MK_QUATRA',
    203018: 'CONST_STAT_ACO_MK_ULTRA',
    203019: 'CONST_STAT_ACO_MK_TEAM',
    203020: 'CONST_STAT_ACO_NOJOY',
    203021: 'CONST_STAT_ACO_REVENGE',
    203022: 'CONST_STAT_ACO_AFTERMATH',
    203023: 'CONST_STAT_ACO_FIRSTBLOOD',
    203024: 'CONST_STAT_ACO_BLUEPLATESPECIAL',
    203025: 'CONST_STAT_ACO_STICKYKILL',
    203026: 'CONST_STAT_ACO_HEADSHOT',
    203027: 'CONST_STAT_ACO_ARTILLERYSTRIKE',
    203028: 'CONST_STAT_ACO_MELEE',
    203029: 'CONST_STAT_ACO_ROADKILL',
    203030: 'CONST_STAT_ACO_FLAG_CAPTURE',
    203031: 'CONST_STAT_ACO_FLAG_GRAB',
    203032: 'CONST_STAT_ACO_BK_GEN',
    203033: 'CONST_STAT_ACO_RABBITKILL',
    203034: 'CONST_STAT_ACO_KILLASRABBIT',
    203035: 'CONST_STAT_ACO_FINALBLOW',
    203036: 'CONST_STAT_ACO_REPAIR',
    203037: 'CONST_STAT_ACO_BK_TURRET',
    203039: 'CONST_STAT_ACO_ASSIST',
    203040: 'CONST_STAT_ACO_FLAG_RETURN',
    203041: 'CONST_STAT_ACO_BK_RADAR',
    203042: 'CONST_STAT_ACO_FLAG_ASSIST',
    203043: 'CONST_STAT_ACO_AIRMAIL',
    203044: 'CONST_STAT_ACO_GAME_COMPLETE',
    203045: 'CONST_STAT_ACO_GAME_WINNER',
    203046: 'CONST_STAT_ACO_FLAG_GRABDM',
    203047: 'CONST_STAT_ACO_FLAG_HOLDER',
    203048: 'CONST_STAT_ACO_FLAG_KILLER',
    203049: 'CONST_STAT_ACO_FLAG_GRABFAST',
    203050: 'CONST_STAT_ACO_DEFENSE_GEN',
    203051: 'CONST_STAT_ACO_DEFENSE_FLAG',
    203052: 'CONST_STAT_ACO_VD_BIKE',
    203053: 'CONST_STAT_ACO_VD_TANK',
    203054: 'CONST_STAT_ACO_VD_SHRIKE',
    203055: 'CONST_STAT_ACO_FLAG_GRABE',
    203056: 'CONST_STAT_ACO_FLAG_GRABLLAMA',
    203057: 'CONST_STAT_ACO_ASSIST_VEHICLE',
    203058: 'CONST_STAT_ACO_FLAG_GRABULTRA',
    203059: 'CONST_STAT_ACO_BENCHEM',
    203060: 'CONST_STAT_ACO_DOUBLEDOWN',
    203061: 'CONST_STAT_ACO_LASTMANSTANDING',
    203062: 'CONST_STAT_ACO_MIRACLE',
    203063: 'CONST_STAT_ACO_NOTAMONGEQUALS',
    203064: 'CONST_STAT_ACO_ONEMANARMY',
    203065: 'CONST_STAT_ACO_TRIBALHONOR',
    203066: 'CONST_STAT_ACO_UNITEDWESTAND',
    203067: 'CONST_STAT_ACO_HOLDTHELINE',
    203068: 'CONST_STAT_ACO_CAPTUREANDHOLD',
    203069: 'CONST_STAT_ACO_BASEASSIST',
    203070: 'CONST_STAT_ACO_TURRETASSIST',
    203071: 'CONST_STAT_ACO_HOTAIR',
    204001: 'CONST_STAT_AWD_CREDITS_EARNED',
    204002: 'CONST_STAT_AWD_CREDITS_SPENT',
    204003: 'CONST_STAT_AWD_DESTRUCTION_DEPLOYABLE',
    204004: 'CONST_STAT_AWD_DESTRUCTION_VEHICLE',
    204005: 'CONST_STAT_AWD_DISTANCE_HEADSHOT',
    204006: 'CONST_STAT_AWD_DISTANCE_KILL',
    204007: 'CONST_STAT_AWD_DISTANCE_SKIED',
    204008: 'CONST_STAT_AWD_KILLS',
    204009: 'CONST_STAT_AWD_KILLS_DEPLOYABLE',
    204010: 'CONST_STAT_AWD_KILLS_MIDAIR',
    204011: 'CONST_STAT_AWD_KILLS_VEHICLE',
    204012: 'CONST_STAT_AWD_REPAIRS',
    204013: 'CONST_STAT_AWD_SPEED_FLAGCAP',
    204014: 'CONST_STAT_AWD_SPEED_FLAGGRAB',
    204015: 'CONST_STAT_AWD_SPEED_SKIED',
    204016: 'CONST_STAT_AWD_FLAG_RETURNS',
    204017: 'CONST_STAT_AWD_DEATHS',
}

class ParseError(Exception):
    def __init__(self, message, bitsleft):
        super().__init__(message)
        self.bitsleft = bitsleft

class ParserState():
    def __init__(self):
        # ID sizes are per-class (probably depends on how many members a class has)
        # - it is guaranteed to be 8 for the FirstServerObject_0
        # - it is guaranteed to be 8 for the TrPlayerController_0
        # - it is guaranteed to be 6 for the TrPlayerReplicationInfo_0
        # - it appears to be 6 for TrGameReplicationInfo_0
        # - it appears to be 7 for TrPlayerPawn_0

        TrInventoryManagerProps = {
            '01111': {'name': 'Instigator',
                       'type': bitarray,
                       'size': 10},
            '11111': {'name': 'Owner',
                       'type': bitarray,
                       'size': 10},
            '10101': {'name': 'InventoryChain',
                       'type': bitarray,
                       'size': 11},
        }

        TrPlayerPawnProps = {
            '1010000': {'name': 'bNetOwner',
                        'type': bool},
            '1101000': {'name': 'RemoteRole',
                        'type': bitarray,
                        'size': 2},
            '1111000': {'name': 'Owner',
                        'type': bitarray,
                        'size': 11},
            '1100100': {'name': 'Rotation',
                        'type': bitarray,
                        'size': 24},
            '1001100': {'name': 'InvManager',
                        'type': bitarray,
                        'size': 11},
            '0111100': {'name': 'PlayerReplicationInfo',
                        'type': bitarray,
                        'size': 11},
            '1111100': {'name': 'HealthMax',
                        'type': int},
            '0000010': {'name': 'Health',
                        'type': int},
            '1000010': {'name': 'AirControl',
                        'type': int},
            '0110010': {'name': 'GroundSpeed',
                        'type': int},
            '1101010': {'name': 'bCanSwatTurn',
                        'type': bool},
            '0011010': {'name': 'bSimulateGravity',
                        'type': bool},
            '1111010': {'name': 'Controller',
                        'type': bitarray,
                        'size': 11},
            # size varies:
            # 10101000000
            # 000
            '1000110': {'name': 'CompressedBodyMatColor',
                        'type': bitarray,
                        'size': 3},
            '0100110': {'name': 'ClientBodyMatDuration',
                        'type': int},
            '0101110': {'name': 'LastTakeHitInfo',
                        'type': bitarray,
                        'size': 139},
            '0111110': {'name': 'unknown int field',
                        'type': int},
            '1001001': {'name': 'CurrentWeaponAttachmentClass',
                        'type': int},
            '1100101': {'name': 'r_fPowerPoolRechargeRate',
                        'type': int},
            '0010101': {'name': 'r_fMaxPowerPool',
                        'type': int},
            '1010101': {'name': 'r_fCurrentPowerPool',
                        'type': int},
            '1000011': {'name': 'r_bDetectedByEnemyScanner',
                        'type': bool},
            '1100011': {'name': 'r_bIsInvulnerable',
                        'type': bool},
            '1110011': {'name': 'r_bIsSkiing',
                        'type': bool},
            '0001011': {'name': 'r_bIsHealthRecharging',
                        'type': bool},
            '0111011': {'name': 'RPC ClientUpdateHUDHealth',
                        'type': [
                            {'name': 'NewHealth',
                             'type': int},
                            {'name': 'NewHealthMax',
                             'type': int}
                        ]},
            '1111011': {'name': 'RPC PlayHardLandingEffect',
                        'type': bitarray,
                        'size': 53},
            '1100111': {'name': 'r_nFlashReloadSecondaryWeapon',
                        'type': bitarray,
                        'size': 8}
        }

        TrDeviceProps = {
            '100001' : { 'name' : 'r_AmmoCount',
                         'type' : bitarray,
                         'size' : 64 },
            '010001' : { 'name' : 'r_bIsReloading',
                         'type' : bool },
            '110001' : { 'name' : 'r_bReadyToFire',
                         'type' : bool },
            '001001' : { 'name' : 'r_eEquipAt',
                         'type' : bitarray,
                         'size' : 4 },
            '000101' : { 'name' : 'r_bTargetLocked',
                         'type' : bool},
            '111101' : { 'name' : 'Owner',
                         'type' : bitarray,
                         'size' : 10 },
            '101011' : { 'name' : 'InvManager',
                         'type' : bitarray,
                         'size' : 10 },
            '011011' : { 'name' : 'Inventory',
                         'type' : bitarray,
                         'size' : 10 },
        }

        TrRadarStationProps = {
            '000111': {'name': 'r_bReset',
                       'type': bitarray,
                       'size': 7},
            '010111': {'name': 'r_ShieldHealth',
                       'type': bitarray,
                       'size': 31}
        }

        TrInventoryStationProps = {
            '000111': {'name': 'r_bReset',
                       'type': bitarray,
                       'size': 7},
        }

        TrRepairStationProps = {
            '000111': {'name': 'r_bReset',
                       'type': bitarray,
                       'size': 7},
        }

        TrVehicleStationProps = {
            '10100': {'name': 'r_nCanSpawnVehicle',
                      'type': bitarray,
                      'size': 33},
            '11111': {'name': 'r_MaxHealth',
                      'type': int},
        }

        # unsure
        TrInventoryStationCollisionProps = {
            # '101100' : { 'name' : 'RelativeLocation2',
            #              'type' : bitarray,
            #              'size' : 2 },
            # '001001' : { 'name' : 'RelativeLocation',
            #              'type' : bitarray,
            #              'size' : 10 },
            # '011111' : { 'name': 'Base',
            #              'type': bitarray,
            #              'size': 30},
        }

        TrPowerGeneratorProps = {
            '00000': {'name': 'r_Health',
                      'type': bitarray,
                      'size': 33},
            '10000': {'name': 'r_nDowntimeRemaining',
                      'type': bitarray,
                      'size': 33},
            '11011': {'name': 'r_bInDestroyedState',
                      'type': bool},
            '00111': {'name': 'r_bIsPowered',
                      'type': bool},
            '00011': {'name': 'r_bReset',
                      'type': bitarray,
                      'size': 8},

            # possible values:
            # 1110 101001011111111110011001001
            # 1110 101001011111111110101101001
            # 1110 101001011111111110001011001
            # 1110 101001011111111110100111001
            # 1110 101001011111111110011000001
            # 1110 101001011111111110101100001
            # 1110 101001011111111110011010001
            # 1110 011111011111111110111010001
            # 1110 101001011111111110011110001
            # 0001 110011001111111111101111000001
            # 0101 100010011011111111111110111110000001
            # 0101 001001101011111111111110011100000001
            '01111': {'name': 'r_vReplicatedHitInfo',
                      'type': 'fvector'},
            '11111': {'name': 'r_MaxHealth',
                      'type': int},
        }

        # TODO: It looks like RPC identifiers are only 6 bits when sent along with properties.
        # When sent along with a counter, we need more bits to distinguish between them.
        TrPlayerControllerProps = {
            '01000000': {'name': 'bCollideWorld',
                         'type': bitarray,
                         'size': 2},
            '11000000': {'name': 'RPC ClientMatchOver',
                         'type': [
                             {'name': 'unknown',
                              'type': 'flag'},
                             {'name': 'Winner',
                              'type': int},
                             {'name': 'WinnerName',
                              'type': str}
                         ]},
            '00100000': {'name': '!!!!!!!!!INTERESTING Unknown INTERESTING!!!!!!!!!',
                         'type': bitarray,
                         'size': 10},
            '00110000': {'name': 'RPC ClientSetLastDamagerInfo',
                         'type': bitarray,
                         'size': 35},
            '10110000': {'name': 'RPC ClientShowOverheadNumber',
                         'type': [
                             {'name': 'unknown',
                              'type': bitarray,
                              'size': 120}
                         ]},
            '01001000': {'name': 'RPC ClientQueueAccolade',
                         'type': [
                             {'name': 'Accolade',
                              'type': bitarray,
                              'size': 33},
                             {'name': 'CreditsAwarded',
                              'type': int}
                         ]},
            # '10001000': {'name': 'RPC ClientPlayerResettingAndRespawning',
            #            'type': bitarray,
            #            'size': 1},
            '10101000': {'name': 'PlayerReplicationInfo',
                         'type': bitarray,
                         'size': 11},
            '01100000': {'name': 'RPC UpdateMatchCountdown',
                         'type': [
                             {'name': 'unknown',
                              'type': 'flag'},
                             {'name': 'Seconds',
                              'type': int}
                         ]},
            '01101000': {'name': 'Pawn',
                         'type': bitarray,
                         'size': 11},
            '00011000': {'name': 'RPC ClientSetRotation',
                         'type': bitarray,
                         'size': 2},
            '01011000': {'name': 'RPC ClientSwitchToBestWeapon',
                         'type': bitarray,
                         'size': 1},
            # # variable length, so currently it screws up what follows
            '00100100': {'name': 'RPC ClientGotoState',
                         'type': [
                             {'name': 'NewState',
                              'type': bitarray,
                              'size': 11},
                             {'name': 'NewLabel',
                              'type': bitarray,
                              'size': 11}
                         ]},
            '01100100': {'name': 'RPC GivePawn',
                         'type': [
                             {'name': 'NewPawn',
                              'type': bitarray,
                              'size': 11}
                         ]},
            # the size of this one varies... these appear to be valid:
            # 1 01100110010011100000000000000000 1 11000000000000000000000000000000 1 11110000000 0 1 10101000000
            # 1 01101100100010010100000000000000 1 10000000000000000000000000000000 0 1 11110000000 1 01000111110001010100000000000000
            # 1 01111111000010110100000000000000 1 00000000100000000000000000000000 1 11110000000 0 0
            # 1 01111111000010110100000000000000 1 10100000000000000000000000000000 0 0 0
            # 1 00000000011111101100000000000000 1 11100000000000000000000000000000 0 0 0
            '10010100': {'name': 'RPC ReceiveLocalizedMessage',
                         'type': [
                             {'name': 'Message',
                              'type': int},
                             {'name': 'Switch',
                              'type': int},
                             {'name': 'RelatedPRI_1',
                              'type': bitarray,
                              'size': 11},
                             {'name': 'RelatedPRI_2',
                              'type': int},
                             {'name': 'OptionalObject',
                              'type': bitarray,
                              'size': 11},
                         ]},
            # '11010100': {'name': 'RPC ClientHearSound',
            #            'type': bitarray,
            #            'size': 48},
            '11011100': {'name': 'RPC VeryShortClientAdjustPosition',
                         'type': [
                             {'name': 'TimeStamp',
                              'type': float},
                             {'name': 'NewLocX',
                              'type': float},
                             {'name': 'NewLocY',
                              'type': float},
                             {'name': 'NewLocZ',
                              'type': float},
                             {'name': 'newBase',
                              'type': bitarray,
                              'size': 32}
                         ]},
            '00111100': {'name': 'RPC ShortClientAdjustPosition',
                         'type': [
                             {'name': 'TimeStamp',
                              'type': float},
                             {'name': 'newState',
                              'type': bitarray,
                              'size': 11},
                             {'name': 'newPhysics',
                              'type': bitarray,
                              'size': 4},
                             {'name': 'NewLocX',
                              'type': float},
                             {'name': 'NewLocY',
                              'type': float},
                             {'name': 'NewLocZ',
                              'type': float},
                             {'name': 'newBase',
                              'type': bitarray,
                              'size': 32}
                         ]},
            '01111100': {'name': 'RPC ClientAckGoodMove',
                         'type': [
                             {'name': 'TimeStamp',
                              'type': float}
                         ]},
            '11111100': {'name': 'RPC ClientAdjustPosition',
                         'type': [
                             {'name': 'TimeStamp',
                              'type': float},
                             {'name': 'newState',
                              'type': bitarray,
                              'size': 11},
                             {'name': 'newPhysics',
                              'type': bitarray,
                              'size': 4},
                             {'name': 'NewLocX',
                              'type': float},
                             {'name': 'NewLocY',
                              'type': float},
                             {'name': 'NewLocZ',
                              'type': float},
                             {'name': 'NewVelX',
                              'type': float},
                             {'name': 'NewVelY',
                              'type': float},
                             {'name': 'NewVelZ',
                              'type': float},
                             {'name': 'newBase',
                              'type': bitarray,
                              'size': 32}
                         ]},

            # reliable client function ClientGameEnded(optional Actor EndGameFocus, optional bool bIsWinner)
            '00110010': {'name': 'RPC ClientGameEnded',
                         'type': bitarray,
                         'size': 2},
#                         'type': [
#                             {'name': 'param1',
#                              'type': bool},
#                             {'name': 'param2',
#                              'type': bool}
#                          ]},
            # 110101110000 100000000000000000000000000000000100000000000000000000000000000000100
            # 110100000000 100000000000000000000000000000000100000000000000000000000000000000100
            # 100001010000 101011110000000000000 100000000000000000000000000000000100000000000000000000000000000000100
            '10110010': {'name': 'RPC ClientSetViewTarget',
                         # 'type': [
                         #     {'name': 'PlayerReplicationInfo',
                         #      'type': bitarray,
                         #      'size': 11},
                         #     {'name':
                         'type': bitarray,
                         'size': 81},
            '11101010': {'name': 'RPC ClientPlayForceFeedbackWaveform',
                         'type': [
                             {'name': 'FFWaveform',
                              'type': int},
                             {'name': 'FFWaveformInstigator',
                              'type': None}
                         ]},
            # '00111010': {'name': 'bNetOwner',
            #            'type': bitarray,
            #            'size': 2},
            '10110110': {'name': 'RPC ClientWriteLeaderboardStats',
                         'type': [
                             {'name': 'OnlineStatsWriteClass',
                              'type': None}
                         ]},
            '11101110': {'name': 'RPC ClientEndOnlineGame',
                         'type': 'flag'},
            # '01110001': {'name': 'Rotation',
            #              'type': bitarray,
            #              'size': 12},
            '01001001': {'name': 'RPC PlayStartupMessage',
                         'type': [
                             {'name': 'StartupStage',
                              'type': bitarray,
                              'size': 8}
                         ]},
            # varies in size:
            # 11110100000011001111001101000110101011111101100000110001010100000000000000
            # 0101111110101011001010001010100000000000000
            '11001001': {'name': 'RPC ClientPlayTakeHit',
                         'type': bitarray,
                         'size': 43},
            # '00101001': {'name': 'RPC ClientSetBehindView',
            #              'type': bitarray,
            #              'size': 1},
            # '11011001': {'name': 'RPC ClientPawnDied',
            #              'type': 'flag'},
            # '00011101': {'name': 'RemoteRole',
            #              'type': bitarray,
            #              'size': 3},
            '01100011': {'name': 'RPC ClientMySaberLauncherTargetingUpdated',
                         'type': [
                             {'name': 'MissileLockValue',
                              'type': bitarray,
                              'size': 3}
                         ]},
            '00101011': {'name': 'RPC ClientEndTeamSelect',
                         'type': [
                             {'name': 'RequestedTeamNum',
                              'type': int}
                         ]},
            '10111101': {'name': 'r_nCurrentCredits',
                         'type': bitarray,
                         'size': 32},
            '01000011': {'name': 'r_bNeedLoadout',
                         'type': bool},
            '11000011': {'name': 'r_bNeedTeam',
                         'type': bool},
            '11100011': {'name': 'RPC ClientSeekingMissileTargetingSelfEvent',
                         'type': [
                             {'name': 'EventSwitch',
                              'type': int}
                         ]},
        }

        TrBaseTurretProps = {
            '010001': {'name': 'r_TargetPawn',
                       'type': bitarray,
                       'size': 11},
            '110001': {'name': 'r_FlashCount',
                       'type': bitarray,
                       'size': 8},
            '000111': {'name': 'r_bReset',
                       'type': bitarray,
                       'size': 7},
            '010111': {'name': 'r_ShieldHealth',
                       'type': bitarray,
                       'size': 31}
        }

        TrCTFBaseProps = {
            '111011': {'name': 'myFlag',
                       'type': bitarray,
                       'size': 10}
        }

        TrProjProps = {
            '00000': {'name': 'Velocity',
                      'type': bitarray,
                      'size': 43 },
            '10000': {'name': 'bCollideActors',
                      'type': bool },
            '11100': {'name': 'bTearOff',
                      'type': bool},
            '10100': {'name': 'bNetOwner',
                      'type': bool},
            '10110': {'name': 'Base',
                      'type': bitarray,
                      'size': 31 },
            '01110': {'name': 'Rotation',
                      'type': bitarray,
                      'size': 19 },
            '10011': {'name': 'r_vSpawnLocation',
                      'type': bitarray,
                      'size': 52},
            '11111': {'name': 'Owner',
                      'type': bitarray,
                      'size': 10}
        }

        TrDroppedPickupProps = {
            '101101' : { 'name' : 'InventoryClass',
                         'type' : bitarray,
                         'size' : 31 },
            '011101' : { 'name' : 'Base',
                         'type' : bitarray,
                         'size' : 30 },
            '110011' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 10 },
            '101011' : { 'name' : 'bFadeOut',
                         'type' : 'flag' }
        }

        TrGameReplicationInfoProps = {
            '000000': {'name': 'netflags',
                       'type': bitarray,
                       'size': 5},
            '001000': {'name': 'GeneratorPower',
                       'type': bitarray,
                       'size': 41},
            '011000': {'name': 'm_Flags',
                       'type': bitarray,
                       'size': 20},
            '101000': {'name': 'r_ServerConfig',
                       'type': bitarray,
                       'size': 12},
            '111000': {'name': 'FlagReturnTime',
                       'type': bitarray,
                       'size': 41},
            '011010': {'name': 'ServerName', 'type': str},
            '111010': {'name': 'TimeLimit', 'type': int},
            '000110': {'name': 'GoalScore', 'type': int},
            '100110': {'name': 'RemainingMinute', 'type': int},
            '010110': {'name': 'ElapsedTime', 'type': int},
            '110110': {'name': 'RemainingTime', 'type': int},
            '101110': {'name': 'bMatchIsOver', 'type': bool},
            '111110': {'name': 'bStopCountDown', 'type': bool},
            '000001': {'name': 'GameClass', 'type': int},
            '100001': {'name': 'MessageOfTheDay', 'type': str},
            '010001': {'name': 'RulesString', 'type': str},
            '001001': {'name': 'FlagState',
                       'type': bitarray,
                       'size': 10,
                       'values': {'0000000000': 'Enemy flag on stand',
                                  '0000000001': 'Enemy flag taken',
                                  '0000000011': 'Enemy flag dropped',
                                  '1000000000': 'Own flag on stand',
                                  '1000000001': 'Own flag taken',
                                  '1000000011': 'Own flag dropped'}},
            '111001': {'name': 'bAllowKeyboardAndMouse', 'type': bool},
            '010101': {'name': 'bWarmupRound', 'type': bool},
            '001101': {'name': 'MinNetPlayers', 'type': int},
            '101111': {'name': 'r_nBlip',
                       'type': bitarray,
                       'size': 8},
        }

        TrFlagCTFProps = {
            '10000' : { 'name' : 'bCollideActors', 'type' : bool},
            '11000' : { 'name' : 'bHardAttach', 'type' : bool},
            '00010' : { 'name' : 'Physics',
                         'type' : bitarray,
                         'size' : 4 },
            '00001' : { 'name' : 'Location',
                         'type' : bitarray,
                         'size' : 52 },
            '10001' : { 'name' : 'RelativeLocation',
                         'type' : bitarray,
                         'size' : 22 },
            '11001' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 11 },
            '00101' : { 'name' : 'Velocity',
                         'type' : bitarray,
                         'size' : 40 },
            '10111' : { 'name' : 'Base',
                         'type' : bitarray,
                         'size' : 10 },
            '01000' : { 'name' : 'bCollideWorld', 'type' : bool},
            '01101' : { 'name' : 'bHome', 'type' : bool},
            '01001' : { 'name' : 'RelativeRotation',
                        'type' : bitarray,
                        'size' : 27 },
            '11101' : { 'name' : 'Team',
                        'type' : bitarray,
                        'size' : 11 },
            '00011' : { 'name' : 'HolderPRI',
                        'type' : bitarray,
                        'size' : 11 }
        }

        TrPlayerReplicationInfoProps = {
            '000000' : { 'name' : 'netflags',
                         'type' : bitarray,
                         'size' : 5 },
            '000010' : { 'name' : 'Location',
                         'type' : bitarray,
                         'size' : 51 },
            '110010' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 10 },
            '101010' : { 'name' : 'UniqueId',
                         'type' : bitarray,
                         'size' : 64 },
            '011010' : { 'name' : 'Unknown field',
                         'type' : int },
            '110110' : { 'name' : 'bWaitingPlayer', 'type' : bool },
            '000110' : { 'name' : 'bBot', 'type' : bool },
            '101110' : { 'name' : 'bIsSpectator', 'type' : bool },
            '111110' : { 'name' : 'Team (11 bits)',
                         'type' : bitarray,
                         'size' : 11,
                         'values' : { '10001000000' : 'DiamondSword',
                                      '11110000000' : 'BloodEagle' } },
            '000001' : { 'name' : 'PlayerID', 'type' : int },
            '100001' : { 'name' : 'PlayerName', 'type' : str },
            '010001' : { 'name' : '???', 'type' : bitarray, 'size': 8 },
            '110001' : { 'name' : 'Deaths', 'type' : int },
            '001001' : { 'name' : 'Score', 'type' : int },
            '011001' : { 'name' : 'CharClassInfo', 'type' : int },
            '010101' : { 'name' : 'bHasFlag', 'type': bool},
            '101101' : { 'name' : 'r_bSkinId', 'type': int},
            '111101' : { 'name' : 'r_EquipLevels',
                         'type' : bitarray,
                         'size' : 48},
            '000011' : { 'name' : 'r_VoiceClass', 'type': int},
            '100011' : { 'name' : 'm_LockedTarget', 'type': bitarray, 'size': 11},
            '001011' : { 'name' : 'm_nPlayerClassId', 'type': int},
            '101011' : { 'name' : 'm_nCreditsEarned', 'type': int},
            '000111' : { 'name' : 'm_nPlayerIconIndex', 'type': int},
            '001111' : { 'name' : 'm_PendingBaseClass', 'type': int},
            '101111' : { 'name' : 'm_CurrentBaseClass', 'type': int},

        }

        TrServerSettingsInfoProps = {
#            '000000': {'name': 'fFriendlyFireDamageMultiplier',
#                       'type': bitarray,
#                       'size': 31},
#            ''
        }

        TrStationCollisionProps = {
            '01110': {'name': 'Base',
                      'type': bitarray,
                      'size': 31},
            # possible values:
            # 00101111110101101111101111001011110000000000000
            '01101': {'name': 'RelativeLocation',
                      'type': 'fvector'},
            '00000': {'name': 'RelativeRotation',
                      'type': bitarray,
                      'size': 25}
        }

        FirstClientObjectProps = {
            '000100' : { 'name' : 'prop8',
                         'type' : bitarray,
                         'size' : 162 },
        }

        FirstServerObjectProps = {
            '10000000': {'name': 'mysteryproperty3',
                         'type': PropertyValueMystery3},
            '11000000': {'name': 'mysteryproperty5',
                         'type': (
                             {'name': 'unknown',
                              'type': int},
                             {'name': 'unknown2',
                              'type': str}
                         )},
            '00100000': {'name': 'mysteryproperty4',
                         'type': (
                             {'name': 'unknown',
                              'type': bitarray,
                              'size': 88},
                             {'name': 'server url',
                              'type': str}
                         )},
            '11100000': {'name': 'mysteryproperty1',
                         'type': PropertyValueMystery1},
            '11010000': {'name': 'mysteryproperty2',
                         'type': PropertyValueMystery2},
            '10111000': {'name': 'interestingproperty',
                         'type': PropertyValueInteresting}
        }

        MatineeActorProps = {
            '00000': {'name': 'netflags',
                      'type': bitarray,
                      'size': 6},
            '11101': {'name': 'Position',
                      'type': bitarray,
                      'size': 32},
            '00011': {'name': 'PlayRate',
                      'type': int},
            '11011': {'name': 'bIsPlaying',
                      'type': bool},
            '00111': {'name': 'InterpAction',
                      'type': bitarray,
                      'size': 32}
        }

        UTTeamInfoFlags = {
            '00000': {'name': 'netflags',
                      'type': bitarray,
                      'size': 6},
            '10101': {'name': 'TeamIndex',
                      'type': int},
            '00011': {'name': 'TeamFlag',
                      'type': bitarray,
                      'size': 11},
            '10011': {'name': 'HomeBase',
                      'type': int}
        }

        WorldInfoProps = {
            '00011': {'name': 'TimeDilation',
                      'type': float},
            '01101': {'name': 'WorldGravityZ',
                      'type': float}
        }

        self.class_dict = {
            None:                               {'name': 'FirstServerObject', 'props': FirstServerObjectProps},
            '00001000100000000111111011011000': {'name': 'FirstClientObject', 'props': FirstClientObjectProps},
            '10001000000000000000000000000000': {'name': 'FirstServerObject', 'props': FirstServerObjectProps},
            '00101100100100010000000000000000': {'name': 'MatineeActor', 'props': MatineeActorProps},
            '00100111010010011000000000000000': {'name': 'UTTeamInfo', 'props': UTTeamInfoFlags},
            '00011100001100100100000000000000': {'name': 'TrBaseTurret_BloodEagle', 'props': TrBaseTurretProps},
            '00111100001100100100000000000000': {'name': 'TrBaseTurret_DiamondSword', 'props': TrBaseTurretProps},
            '01111110111001011110000000000000': {'name': 'TrCTFBase_BloodEagle', 'props': TrCTFBaseProps},
            '00111110111001011110000000000000': {'name': 'TrCTFBase_DiamondSword', 'props': TrCTFBaseProps},
            '01010111000101011110000000000000': {'name': 'TrCTFBase_BloodEagle', 'props': TrCTFBaseProps},
            '00110111000101011110000000000000': {'name': 'TrCTFBase_DiamondSword', 'props': TrCTFBaseProps},
            '01111000100110010100000000000000': {'name': 'TrDevice_Blink', 'props': TrDeviceProps},
            '01000011100110010100000000000000': {'name': 'TrDevice_ConcussionGrenade', 'props': TrDeviceProps},
            '00110000010110010100000000000000': {'name': 'TrDevice_ElfFlak', 'props': TrDeviceProps},
            '01101001110110010100000000000000': {'name': 'TrDevice_Grenade', 'props': TrDeviceProps},
            '01100101110110010100000000000000': {'name': 'TrDevice_GrenadeLauncher_Light', 'props': TrDeviceProps},
            '00100100001110010100000000000000': {'name': 'TrDevice_HeavyBoltLauncher', 'props': TrDeviceProps},
            '00110100001110010100000000000000': {'name': 'TrDevice_HeavyShieldPack', 'props': TrDeviceProps},
            '00111001001110010100000000000000': {'name': 'TrDevice_Twinfusor', 'props': TrDeviceProps},
            '01001000101110010100000000000000': {'name': 'TrDevice_LaserTargeter', 'props': TrDeviceProps},
            '01101100101110010100000000000000': {'name': 'TrDevice_LightAssaultRifle', 'props': TrDeviceProps},
            '01111100101110010100000000000000': {'name': 'TrDevice_LightSpinfusor', 'props': TrDeviceProps},
            '00100111101110010100000000000000': {'name': 'TrDevice_Melee_DS', 'props': TrDeviceProps},
            '01101001000001010100000000000000': {'name': 'TrDevice_SpikeLauncher', 'props': TrDeviceProps},
            '01011001000001010100000000000000': {'name': 'TrDevice_Spinfusor_100X', 'props': TrDeviceProps},
            '01011000100001010100000000000000': {'name': 'TrDevice_UtilityPack_Soldier', 'props': TrDeviceProps},
            '01110101110110010100000000000000': {'name': 'TrDevice_GrenadeXL', 'props': TrDeviceProps},
            '01110111111110010100000000000000': {'name': 'TrDevice_SaberLauncher', 'props': TrDeviceProps},
            '01001011001001010100000000000000': {'name': 'TrDroppedPickup', 'props': TrDroppedPickupProps},
            '00100100101111010100000000000000': {'name': 'TrFlagCTF_BloodEagle', 'props': TrFlagCTFProps},
            '00110100101111010100000000000000': {'name': 'TrFlagCTF_DiamondSword', 'props': TrFlagCTFProps},
            '01110001101110110100000000000000': {'name': 'TrGameReplicationInfo', 'props': TrGameReplicationInfoProps},
            '01101101010100001100000000000000': {'name': 'TrInventoryManager', 'props': TrInventoryManagerProps},
            '01010000100101011110000000000000': {'name': 'TrInventoryStation_BloodEagle0101?', 'props': TrInventoryStationProps},
            '01000000100101011110000000000000': {'name': 'TrInventoryStation_BloodEagle0100?', 'props': TrInventoryStationProps},
            '01100000100101011110000000000000': {'name': 'TrInventoryStation_BloodEagle0110?', 'props': TrInventoryStationProps},
            '00100000100101011110000000000000': {'name': 'TrInventoryStation_BloodEagle0010?', 'props': TrInventoryStationProps},
            #'00010010100101011110000000000000': {'name': 'TrInventoryStation_BloodEagle0001?', 'props': TrInventoryStationProps},
            '01001000100101011110000000000000': {'name': 'TrInventoryStation_DiamondSword', 'props': TrInventoryStationProps},
            '01001011110100001100000000000000': {'name': 'TrInventoryStationCollision', 'props': TrInventoryStationCollisionProps},
            '00110001010000010100000000000000': {'name': 'TrPlayerController', 'props': TrPlayerControllerProps},
            '00111010100001100100000000000000': {'name': 'TrPlayerPawn', 'props': TrPlayerPawnProps},
            '00000110101111001100000000000000': {'name': 'TrPlayerReplicationInfo', 'props': TrPlayerReplicationInfoProps},
            '01111010010000101100000000000000': {'name': 'TrProj_BaseTurret', 'props': TrProjProps},
            '00000001110000101100000000000000': {'name': 'TrProj_ElfFlak', 'props': TrProjProps},
            '01011111110000101100000000000000': {'name': 'TrProj_HeavyBoltLauncher', 'props': TrProjProps},
            '01100010111000101100000000000000': {'name': 'TrProj_SpikeLauncher', 'props': TrProjProps},
            '01010010111000101100000000000000': {'name': 'TrProj_SpikeLauncherSecondary', 'props': TrProjProps},
            '01110010111000101100000000000000': {'name': 'TrProj_SpikeLauncherThird', 'props': TrProjProps},
            '00101010111000101100000000000000': {'name': 'TrProj_Spinfusor_100X', 'props': TrProjProps},
            '01110010100010101100000000000000': {'name': 'TrRadarStation_BloodEagle', 'props': TrRadarStationProps},
            '01001010100010101100000000000000': {'name': 'TrRadarStation_DiamondSword', 'props': TrRadarStationProps},
            '00000000110010101100000000000000': {'name': 'TrRepairStationCollision', 'props': TrRepairStationProps},
            '00010011100001101100000000000000': {'name': 'TrServerSettingsInfo', 'props': TrServerSettingsInfoProps},
            '00000011110100001100000000000000': {'name': 'TrStationCollision', 'props': TrStationCollisionProps},
            '00100010100101011110000000000000': {'name': 'TrRepairStation_BloodEagle0010?', 'props': TrRepairStationProps},
            '01010010100101011110000000000000': {'name': 'TrRepairStation_BloodEagle0101?', 'props': TrRepairStationProps},
            '00110010100101011110000000000000': {'name': 'TrRepairStation_BloodEagle0011?', 'props': TrRepairStationProps},
            '01100010100101011110000000000000': {'name': 'TrRepairStation_BloodEagle0110?', 'props': TrRepairStationProps},
            '01011010100101011110000000000000': {'name': 'TrRepairStation_DiamondSword', 'props': TrRepairStationProps},
            '00000011111001011110000000000000': {'name': 'TrVehicleStation_DiamondSword', 'props': TrVehicleStationProps},
            '00100110100101011110000000000000': {'name': 'TrVehicleStation_BloodEagle', 'props': TrVehicleStationProps},
            '01111101111001011110000000000000': {'name': 'TrVehicleStation_BloodEagle', 'props': TrVehicleStationProps},
            '01100110100101011110000000000000': {'name': 'TrVehicleStation_DiamondSword', 'props': TrVehicleStationProps},
            '01010101111001011110000000000000': {'name': 'TrPowerGenerator_BloodEagle', 'props': TrPowerGeneratorProps},
            '00111100100101011110000000000000': {'name': 'TrPowerGenerator_BloodEagle', 'props': TrPowerGeneratorProps},
            '01111100100101011110000000000000': {'name': 'TrPowerGenerator_DiamondSword', 'props': TrPowerGeneratorProps},
            '00110101111001011110000000000000': {'name': 'TrPowerGenerator_DiamondSword', 'props': TrPowerGeneratorProps},
            '00101000000101011110000000000000': {'name': 'WorldInfo', 'props': WorldInfoProps},
            '00000101100101011110000000000000': {'name': 'WorldInfo', 'props': WorldInfoProps},
        }

        self.instance_count = {}
        self.channels = {}


def int2bitarray(n, nbits):
    bits = bitarray(endian='little')
    bits.frombytes(struct.pack('<L', n))
    return bits[:nbits]

def toint(bits):
    zerobytes = bytes( (0,0,0,0) )
    longbytes = (bits.tobytes() + zerobytes)[0:4]
    return struct.unpack('<L', longbytes)[0]

def float2bitarray(val):
    bits = bitarray(endian='little')
    bits.frombytes(struct.pack('<f', val))
    return bits

def tofloat(bits):
    return struct.unpack('<f', bits.tobytes())[0]

def getnbits(n, bits):
    if n > len(bits):
        raise ParseError('Tried to get more bits (%d) than are available (%d)' %
                             (n, len(bits)),
                         bits)
    
    return bits[0:n], bits[n:]

def getstring(bits):
    stringbytes = bits.tobytes()
    result = []
    for b in stringbytes:
        if b != 0:
            result.append(chr(b))
        else:
            break

    return ''.join(result), bits[(len(result) + 1) * 8:]

def debugbits(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        bitsbefore = args[1]
        debug = kwargs['debug']

        if debug:
            print('%s::frombitarray (entry): starting with %s%s' %
                  (self.__class__.__name__,
                   bitsbefore.to01()[0:32],
                   '...' if len(bitsbefore) > 32 else ' EOF'))
        bitsafter = func(*args, **kwargs)

        if debug:
            nbits_consumed = len(bitsbefore) - len(bitsafter)
            if bitsbefore[nbits_consumed:] != bitsafter:
                raise RuntimeError('Function not returning a tail of the input bits')
            print('%s::frombitarray (exit) : consumed \'%s\'' %
                  (self.__class__.__name__, bitsbefore.to01()[:nbits_consumed]))

            if bitsbefore[:nbits_consumed] != self.tobitarray():
                raise RuntimeError('Object %s serialized into bits is not equal to bits parsed:\n' % repr(self) +
                                   'in : %s\n' % bitsbefore[:nbits_consumed].to01() +
                                   'out: %s\n' % self.tobitarray().to01())

        return bitsafter
    
    return wrapper


class PropertyValueMultipleChoice():
    def __init__(self):
        self.value = None
        self.valuebits = None

    @debugbits
    def frombitarray(self, bits, size, values, debug = False):
        self.valuebits, bits = getnbits(size, bits)
        self.value = values.get(self.valuebits.to01(), 'Unknown')
        return bits

    def tobitarray(self):
        return self.valuebits if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %s)\n' % (indent_prefix,
                                            self.valuebits.to01(),
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueString():
    def __init__(self):
        self.size = None
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        stringsizebits, bits = getnbits(32, bits)
        self.size = toint(stringsizebits)

        if self.size > 0:
            self.value, bits = getstring(bits)

            if len(self.value) + 1 != self.size:
                raise ParseError('ERROR: string size (%d) was not equal to expected size (%d)' %
                                     (len(self.value) + 1,
                                      self.size),
                                 bits)
        else:
            self.value = ''

        return bits

    def tobitarray(self):
        if self.value is not None:
            bits = int2bitarray(self.size, 32)
            if self.size > 0:
                bits.frombytes(bytes(self.value, encoding = 'latin1'))
                bits.extend('00000000')
        else:
            bits = bitarray()
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (strsize = %d)\n' % (indent_prefix, int2bitarray(self.size, 32).to01(), self.size)

            if self.size > 0:
                indent_prefix += ' ' * 32        
                text += '%sx (value = "%s")\n' % (indent_prefix,
                                                  self.value)
        else:
            text = '%sempty\n' % indent_prefix
            
        return text

class PropertyValueVector():
    def __init__(self):
        self.short1 = None
        self.short2 = None
        self.short3 = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(16, bits)
        self.short1 = toint(valuebits)
        valuebits, bits = getnbits(16, bits)
        self.short2 = toint(valuebits)
        valuebits, bits = getnbits(16, bits)
        self.short3 = toint(valuebits)
        return bits

    def tobitarray(self):
        if self.short3 is not None:
            return (int2bitarray(self.short1, 16) +
                    int2bitarray(self.short2, 16) +
                    int2bitarray(self.short3, 16))
        else:
            return bitarray()
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.short3 is not None:
            return '%s%s (value = (%d,%d,%d))\n' % (indent_prefix,
                                                    self.tobitarray().to01(),
                                                    self.short1,
                                                    self.short2,
                                                    self.short3)
        else:
            return '%sempty\n' % indent_prefix

class PropertyValueInt():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(32, bits)
        self.value = toint(valuebits)
        return bits

    def tobitarray(self):
        return int2bitarray(self.value, 32) if self.value is not None else bitarray()
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %d %08X%s)\n' % (indent_prefix,
                                                   self.tobitarray().to01(),
                                                   self.value,
                                                   self.value,
                                                   (' %s' % known_int_values.get(self.value, 'unknown')) if self.value in known_int_values else '')
        else:
            text = '%sempty\n' % indent_prefix
        return text


class PropertyValueFloat():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug=False):
        valuebits, bits = getnbits(32, bits)
        self.value = tofloat(valuebits)
        return bits

    def tobitarray(self):
        return float2bitarray(self.value) if self.value is not None else bitarray()

    def tostring(self, indent=0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %f)\n' % (indent_prefix,
                                            self.tobitarray().to01(),
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text


class PropertyValueBool():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(1, bits)
        self.value = (valuebits[0] == 1)
        return bits

    def tobitarray(self):
        return bitarray([self.value]) if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %s)\n' % (indent_prefix,
                                            '1' if self.value else '0',
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueFlag():
    def __init__(self):
        pass

    @debugbits
    def frombitarray(self, bits, debug = False):
        return bits

    def tobitarray(self):
        return bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = '%s(flag is set)\n' % indent_prefix
        return text
        
class PropertyValueBitarray():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, size, debug = False):
        self.value, bits = getnbits(size, bits)
        return bits

    def tobitarray(self):
        return self.value if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value)\n' % (indent_prefix, self.value.to01())
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueFVector():
    def __init__(self):
        self.vectorbits = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        assert len(bits) > 4
        lengthbits, bits = getnbits(4, bits)
        length = toint(lengthbits) * 3 + 6
        self.vectorbits, bits = getnbits(length, bits)
        return bits

    def tobitarray(self):
        length = int((len(self.vectorbits) - 6) / 3)
        lengthbits = int2bitarray(length, 4)
        return lengthbits + self.vectorbits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.vectorbits is not None:
            length = int((len(self.vectorbits) - 6) / 3)
            lengthbits = int2bitarray(length, 4)
            text = '%s%s %s (FVector)\n' % (indent_prefix, lengthbits.to01(), self.vectorbits.to01())
        else:
            text = '%sempty\n' % indent_prefix
        return text


class PropertyValueMystery1():
    def __init__(self):
        self.int1 = PropertyValueInt()
        self.int2 = PropertyValueInt()
        self.int3 = PropertyValueInt()
        self.int4 = PropertyValueInt()
        self.string1 = PropertyValueString()
        self.string2 = PropertyValueString()
        self.int5 = PropertyValueInt()
        self.int6 = PropertyValueInt()
        self.string3 = PropertyValueString()

    @debugbits
    def frombitarray(self, bits, debug = False):
        bits = self.int1.frombitarray(bits, debug = debug)
        bits = self.int2.frombitarray(bits, debug = debug)
        bits = self.int3.frombitarray(bits, debug = debug)
        bits = self.int4.frombitarray(bits, debug = debug)
        bits = self.string1.frombitarray(bits, debug = debug)
        bits = self.string2.frombitarray(bits, debug = debug)
        bits = self.int5.frombitarray(bits, debug = debug)
        bits = self.int6.frombitarray(bits, debug = debug)
        bits = self.string3.frombitarray(bits, debug = debug)
        return bits

    def tobitarray(self):
        return (self.int1.tobitarray() +
                self.int2.tobitarray() +
                self.int3.tobitarray() +
                self.int4.tobitarray() +
                self.string1.tobitarray() +
                self.string2.tobitarray() +
                self.int5.tobitarray() +
                self.int6.tobitarray() +
                self.string3.tobitarray())

    def tostring(self, indent = 0):
        items = []
        items.append(self.int1.tostring(indent))
        items.append(self.int2.tostring(indent))
        items.append(self.int3.tostring(indent))
        items.append(self.int4.tostring(indent))
        items.append(self.string1.tostring(indent))
        items.append(self.string2.tostring(indent))
        items.append(self.int5.tostring(indent))
        items.append(self.int6.tostring(indent))
        items.append(self.string3.tostring(indent))
        text = ''.join(items)
        return text

class PropertyValueMystery2():
    def __init__(self):
        self.string1 = PropertyValueString()
        self.string2 = PropertyValueString()
        self.string3 = PropertyValueString()

    @debugbits
    def frombitarray(self, bits, debug = False):
        bits = self.string1.frombitarray(bits, debug = debug)
        bits = self.string2.frombitarray(bits, debug = debug)
        bits = self.string3.frombitarray(bits, debug = debug)
        return bits

    def tobitarray(self):
        return (self.string1.tobitarray() +
                self.string2.tobitarray() +
                self.string3.tobitarray())

    def tostring(self, indent = 0):
        items = []
        items.append(self.string1.tostring(indent))
        items.append(self.string2.tostring(indent))
        items.append(self.string3.tostring(indent))
        text = ''.join(items)
        return text

class PropertyValueMystery3():
    def __init__(self):
        self.string1 = PropertyValueString()
        self.string2 = PropertyValueString()

    @debugbits
    def frombitarray(self, bits, debug = False):
        bits = self.string1.frombitarray(bits, debug = debug)
        bits = self.string2.frombitarray(bits, debug = debug)
        return bits

    def tobitarray(self):
        return (self.string1.tobitarray() +
                self.string2.tobitarray())

    def tostring(self, indent = 0):
        items = []
        items.append(self.string1.tostring(indent))
        items.append(self.string2.tostring(indent))
        text = ''.join(items)
        return text

class PropertyValueArray:
    def __init__(self):
        self.length = None
        self.fields = []

    @debugbits
    def frombitarray(self, bits, debug=False):
        lengthbits, bits = getnbits(16, bits)
        self.length = toint(lengthbits)

        self.fields = []
        for i in range(self.length):
            field = PropertyValueField()
            self.fields.append(field)
            bits = field.frombitarray(bits, debug=debug)

        return bits

    def tobitarray(self):
        bits = int2bitarray(self.length, 16)
        for field in self.fields:
            bits.extend(field.tobitarray())
        return bits

    def tostring(self, indent=0):
        indent_prefix = ' ' * indent
        if self.length is not None:
            text = '%s%s (length = %d)\n' % (indent_prefix, int2bitarray(self.length, 16).to01(), self.length)

            for field in self.fields:
                text += field.tostring(indent + 4)
        else:
            text = '%sempty\n' % indent_prefix

        return text


class PropertyValueArrayOfArrays:
    def __init__(self):
        self.length = None
        self.arrays = []

    @debugbits
    def frombitarray(self, bits, debug=False):
        lengthbits, bits = getnbits(16, bits)
        self.length = toint(lengthbits)

        self.arrays = []
        for i in range(self.length):
            array = PropertyValueArray()
            self.arrays.append(array)
            bits = array.frombitarray(bits, debug=debug)

        return bits

    def tobitarray(self):
        bits = int2bitarray(self.length, 16)
        for array in self.arrays:
            bits.extend(array.tobitarray())
        return bits

    def tostring(self, indent=0):
        indent_prefix = ' ' * indent
        if self.length is not None:
            text = '%s%s (length = %d)\n' % (indent_prefix, int2bitarray(self.length, 16).to01(), self.length)

            for array in self.arrays:
                text += array.tostring(indent + 4)
        else:
            text = '%sempty\n' % indent_prefix

        return text



class PropertyValueField:
    fieldmap = {
        '0000111010000000': PropertyValueArrayOfArrays,
        '1111011010000000': PropertyValueArrayOfArrays,
        '0011011000100000': 64,
        '1101100100100000': PropertyValueFloat
    }

    def __init__(self):
        self.ident = None
        self.data = None

    @debugbits
    def frombitarray(self, bits, debug=False):
        idbits, bits = getnbits(16, bits)
        self.ident = toint(idbits)

        if idbits.to01() in self.fieldmap:
            fielddef = self.fieldmap[idbits.to01()]
            if isinstance(fielddef, int):
                self.data, bits = getnbits(fielddef, bits)
            else:
                self.data = fielddef()
                bits = self.data.frombitarray(bits, debug=debug)
        else:
            self.data = PropertyValueInt()
            bits = self.data.frombitarray(bits, debug=debug)

        return bits

    def tobitarray(self):
        bits = int2bitarray(self.ident, 16)
        if isinstance(self.data, bitarray):
            bits.extend(self.data)
        else:
            bits.extend(self.data.tobitarray())
        return bits

    def tostring(self, indent=0):
        indent_prefix = ' ' * indent
        if self.ident is not None:
            text = '%s%s (field ident = %04X)\n' % (indent_prefix, int2bitarray(self.ident, 16).to01(), self.ident)
            if isinstance(self.data, bitarray):
                text += '%s%s (field value)\n' % (' ' * (indent + 16), self.data.to01())
            else:
                text += self.data.tostring(indent + 16)
        else:
            text = '%sempty\n' % indent_prefix

        return text


class PropertyValueInteresting:
    def __init__(self):
        self.prefixbits = None
        self.length = None
        self.fields = []

    @debugbits
    def frombitarray(self, bits, debug=False):
        self.prefixbits, bits = getnbits(44, bits)

        lengthbits, bits = getnbits(16, bits)
        self.length = toint(lengthbits)

        self.fields = []
        for i in range(self.length):
            field = PropertyValueField()
            self.fields.append(field)
            bits = field.frombitarray(bits, debug=debug)

        return bits

    def tobitarray(self):
        bits = self.prefixbits[:]
        bits.extend(int2bitarray(self.length, 16))
        for field in self.fields:
            bits.extend(field.tobitarray())
        return bits

    def tostring(self, indent=0):
        indent_prefix = ' ' * indent
        if self.prefixbits is not None:
            text = '%s%s (prefix)\n' % (indent_prefix, self.prefixbits.to01())
            text += '%s%s (number of fields = %d)\n' % (indent_prefix, int2bitarray(self.length, 16).to01(), self.length)

            for field in self.fields:
                text += field.tostring(indent)
        else:
            text = '%sempty\n' % indent_prefix

        return text


def parse_basic_property(propertyname, propertytype, bits, size=None, debug=False):
    if propertytype is str:
        value = PropertyValueString()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype is int:
        value = PropertyValueInt()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype is float:
        value = PropertyValueFloat()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype is bool:
        value = PropertyValueBool()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype is 'flag':
        value = PropertyValueFlag()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype is bitarray:
        value = PropertyValueBitarray()
        #if size is None:
        #    raise RuntimeError("Coding error: size can't be None for bitarray")
        bits = value.frombitarray(bits, size, debug=debug)
    elif propertytype == 'fvector':
        value = PropertyValueFVector()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype == PropertyValueMystery1:
        value = PropertyValueMystery1()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype == PropertyValueMystery2:
        value = PropertyValueMystery2()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype == PropertyValueMystery3:
        value = PropertyValueMystery3()
        bits = value.frombitarray(bits, debug=debug)
    elif propertytype == PropertyValueInteresting:
        value = PropertyValueInteresting()
        bits = value.frombitarray(bits, debug=debug)
    else:
        raise RuntimeError('Coding error: propertytype of property %s has invalid value: %s' % (propertyname, propertytype))

    return value, bits


class PropertyValueStruct():
    def __init__(self, member_list):
        self.member_list = member_list
        self.values = []

    @debugbits
    def frombitarray(self, bits, debug = False):
        self.values = []
        for member in self.member_list:
            propertyname = member.get('name', None)
            propertytype = member.get('type', None)
            propertysize = member.get('size', None)
            value, bits = parse_basic_property(propertyname, propertytype, bits, propertysize, debug = debug)
            self.values.append(value)

        return bits

    def tobitarray(self):
        allbits = bitarray()
        for member in self.values:
            allbits += member.tobitarray()
        return allbits

    def tostring(self, indent = 0):
        items = []
        for member, value in zip(self.member_list, self.values):
            items.append(value.tostring(indent)[:-1] + '(%s)\n' % member['name'])
        text = ''.join(items)
        return text


class PropertyValueParams():
    def __init__(self, param_list):
        self.param_list = param_list
        self.presence = []
        self.values = []

    @debugbits
    def frombitarray(self, bits, debug = False):

        self.values = []
        for member in self.param_list:
            propertyname = member.get('name', None)
            propertytype = member.get('type', None)
            propertysize = member.get('size', None)

            present, bits = getnbits(1, bits)
            self.presence.append(present[0])
            if present[0] == 1:
                value, bits = parse_basic_property(propertyname, propertytype, bits, propertysize, debug = debug)
            else:
                value = None
            self.values.append(value)

        return bits

    def tobitarray(self):
        allbits = bitarray()
        for present, value in zip_longest(self.presence, self.values):
            if present:
                allbits += bitarray([1])
                if value is not None:
                    allbits += value.tobitarray()
            else:
                allbits += bitarray([0])
        return allbits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        for member, present, value in zip_longest(self.param_list, self.presence, self.values):
            if present:
                items.append('%s1 (%s param present)\n' % (indent_prefix, member['name']))
                if value is not None:
                    items.append(value.tostring(indent)[:-1] + '(%s)\n' % member['name'])
            else:
                items.append('%s0 (%s param absent)\n' % (indent_prefix, member['name']))
        text = ''.join(items)
        return text


class ObjectProperty():
    def __init__(self, id_size = 6):
        self.propertyid_size = id_size
        self.propertyid = None
        self.property_ = { 'name' : 'Unknown' }
        self.value = None

    @debugbits
    def frombitarray(self, bits, class_, debug = False):
        propertyidbits, bits = getnbits(self.propertyid_size, bits)
        self.propertyid = toint(propertyidbits)
        
        propertykey = propertyidbits.to01()
        property_ = class_['props'].get(propertykey, {'name' : 'Unknown'})
        self.property_ = property_

        propertyname = property_.get('name', None)
        propertytype = property_.get('type', None)
        propertysize = property_.get('size', None)
        propertyvalues = property_.get('values', None)
        if propertyvalues:
            self.value = PropertyValueMultipleChoice()
            bits = self.value.frombitarray(bits, propertysize, propertyvalues, debug = debug)
        
        elif propertytype:
            if isinstance(propertytype, list):
                self.value = PropertyValueParams(propertytype)
                bits = self.value.frombitarray(bits, debug=debug)
            elif isinstance(propertytype, tuple):
                self.value = PropertyValueStruct(propertytype)
                bits = self.value.frombitarray(bits, debug=debug)
            else:
                try:
                    self.value, bits = parse_basic_property(propertyname, propertytype, bits, propertysize, debug = debug)
                except:
                    self.value = PropertyValueBitarray()
                    raise
        else:
            raise ParseError('Unknown property %s for class %s' %
                                 (propertykey, class_['name']),
                             bits)
        
        return bits

    def tobitarray(self):
        bits = bitarray(endian='little')
        if self.propertyid is not None:
            bits.extend(int2bitarray(self.propertyid, self.propertyid_size))
        if self.value is not None:
            bits.extend(self.value.tobitarray())
        return bits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = ''
        if self.propertyid is not None:
            propertykey = int2bitarray(self.propertyid, self.propertyid_size).to01()
            text += '%s%s (property = %s)\n' % (indent_prefix,
                                               propertykey,
                                               self.property_['name'])
        if self.value is not None:
            text += self.value.tostring(indent = indent + len(propertykey))
        return text

class ObjectInstance():
    def __init__(self, is_rpc = False):
        self.class_ = None
        self.properties = []
        self.is_rpc = is_rpc
    
    @debugbits
    def frombitarray(self, bits, class_, state, debug = False):
        
        while bits:
            property_ = ObjectProperty(id_size = class_['idsize'])
            self.properties.append(property_)
            bits = property_.frombitarray(bits, class_, debug = debug)

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        for prop in self.properties:
            bits.extend(prop.tobitarray())
        return bits
    
    def tostring(self, indent = 0):
        items = [prop.tostring(indent) for prop in self.properties]
        return ''.join(items)

class ObjectClass():
    def __init__(self):
        self.classid = None

    def getclasskey(self):
        classbits = int2bitarray(self.classid, 32)
        if classbits[0:5] == bitarray('10001'):
            classbits[5:] = False
        return classbits.to01()

    @debugbits
    def frombitarray(self, bits, state, debug = False):
        classbits, bits = getnbits(32, bits)
        self.classid = toint(classbits)
        
        classkey = self.getclasskey()
        if classkey not in state.class_dict:
            classname = 'unknown%d' % len(state.class_dict)
            state.class_dict[classkey] = { 'name' : classname,
                                           'props' : {} }

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        if self.classid is not None:
            bits.extend(int2bitarray(self.classid, 32))
        return bits

class PayloadData():

    def __init__(self, reliable = False):
        self.reliable = reliable
        self.size = None
        self.object_class = None
        self.object_deleted = False
        self.instancename = None
        self.instance = None
        self.bitsleftreason = None
        self.bitsleft = None

    @debugbits
    def frombitarray(self, bits, channel, state, debug = False):
        payloadsizebits, bits = getnbits(14, bits)

        if toint(payloadsizebits) >= toint(bitarray('00000000001101', endian='little')):
            payloadsizebits = payloadsizebits[:-1]
            bits.insert(0, True)

        self.nr_of_payload_bits = len(payloadsizebits)
        self.size = toint(payloadsizebits)

        payloadbits, bits = getnbits(self.size, bits)
        originalpayloadbits = bitarray(payloadbits)

        try:
            if channel not in state.channels:
                newinstance = True
                self.object_class = ObjectClass()
                payloadbits = self.object_class.frombitarray(payloadbits, state, debug = debug)

                class_ = state.class_dict[self.object_class.getclasskey() if channel != 0 else None]
                classname = class_['name']

                prop_keys = list(class_['props'].keys())
                class_['idsize'] = len(prop_keys[0]) if prop_keys else 6

                state.instance_count[classname] = state.instance_count.get(classname, -1) + 1
                instancename = '%s_%d' % (classname, state.instance_count[classname])
                state.channels[channel] = { 'class' : class_,
                                            'instancename' : instancename }
            else:
                newinstance = False
                class_ = state.channels[channel]['class']
                instancename = state.channels[channel]['instancename']

            self.instancename = instancename
            self.instance = ObjectInstance(is_rpc = self.reliable and not newinstance)
            payloadbits = self.instance.frombitarray(payloadbits, class_, state, debug = debug)
            
            if payloadbits:
                raise ParseError('Bits of payload left over',
                                 payloadbits)

            if self.size == 0:
                self.object_deleted = True
                del state.channels[channel]
            
        except ParseError as e:
            self.bitsleftreason = str(e)
            self.bitsleft = e.bitsleft

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')

        if self.size is not None:
            bits.extend(int2bitarray(self.size, self.nr_of_payload_bits))
        if self.object_class is not None:
            bits.extend(self.object_class.tobitarray())
        if self.instance is not None:
            bits.extend(self.instance.tobitarray())
        if self.bitsleft is not None:
            bits.extend(self.bitsleft)
            
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = ''

        if self.size is not None:      
            text += ('%s%s (payloadsize = %d)\n' % (indent_prefix,
                                                    int2bitarray(self.size, self.nr_of_payload_bits).to01(),
                                                    self.size))
            indent += self.nr_of_payload_bits
            
        if self.object_class is not None:
            text += '%s%s (new object %s)\n' % (' ' * indent,
                                                self.object_class.tobitarray().to01(),
                                                self.instancename)
            indent += 32
        elif self.object_deleted:
            text += '%sx (destroyed object = %s)\n' % (' ' * indent,
                                                       self.instancename)
            indent += 1
        else:
            text += '%sx (object = %s)\n' % (' ' * indent,
                                             self.instancename)
            indent += 1

        if self.instance is not None:
            text += self.instance.tostring(indent = indent)
            
        if self.bitsleft is not None:
            text += ' ' * indent + self.bitsleft.to01() + ' (rest of payload)\n'
            
        return text

class ChannelData():
    def __init__(self):
        self.channel = None
        self.counter = None
        self.unknownbits = None
        self.payload = None

    @debugbits
    def frombitarray(self, bits, with_counter, state, debug = False):
        channelbits, bits = getnbits(10, bits)
        self.channel = toint(channelbits)

        if with_counter:
            counterbits, bits = getnbits(5, bits)
            self.counter = toint(counterbits)

            self.unknownbits, bits = getnbits(8, bits)

        self.payload = PayloadData(reliable = with_counter)
        bits = self.payload.frombitarray(bits, self.channel, state, debug = debug)
        return bits

    def tobitarray(self):
        bits = int2bitarray(self.channel, 10)
        if self.counter is not None:
            bits.extend(int2bitarray(self.counter, 5))
            bits.extend(self.unknownbits)
        bits.extend(self.payload.tobitarray())
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        items.append('%s (channel = %d)\n' % (int2bitarray(self.channel, 10).to01(),
                                              self.channel))
        indent += 10
        if self.counter is not None:
            items.append('          %s (counter = %d)\n' %
                         (int2bitarray(self.counter, 5).to01(),
                          self.counter))
            items.append('               %s\n' % self.unknownbits.to01())
            indent += 13
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        text += self.payload.tostring(indent = indent)
        return text

class PacketData():
    def __init__(self):
        self.flag1a = None
        self.unknownbits11 = None
        self.unknownbits10 = None
        self.channel_data = None

    @debugbits
    def frombitarray(self, bits, state, debug = False):

        self.flag1a, bits = getnbits(2, bits)
        if self.flag1a == bitarray('11'):
            self.unknownbits11 = True
            self.flag1a = None
            self.flag1a, bits = getnbits(2, bits)

        if self.flag1a == bitarray('00'):
            channel_with_counter = False
        elif self.flag1a == bitarray('01'):
            channel_with_counter = True
        elif self.flag1a == bitarray('10'):
            channel_with_counter = True
            self.unknownbits10, bits = getnbits(2, bits)
            if self.unknownbits10 != bitarray('11'):
                raise ParseError('Unexpected value for unknownbits10: %s' %
                                     self.unknownbits10.to01(),
                                 bits)
            
        else:
            raise ParseError('Unexpected value for flag1a: %s' % self.flag1a.to01(),
                             bits)

        self.channel_data = ChannelData()
        bits = self.channel_data.frombitarray(bits, channel_with_counter, state, debug = debug)
            
        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        if self.unknownbits11:
            bits.extend('11')
        if self.flag1a:
            bits.extend(self.flag1a)
        if self.unknownbits10 is not None:
            bits.extend(self.unknownbits10)

        if self.channel_data:
            bits.extend(self.channel_data.tobitarray())

        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        if self.unknownbits11 is not None:
            items.append('11 (flag1a = 3)\n')
        if self.flag1a is not None:
            items.append('%s (flag1a = %d)\n' % (self.flag1a.to01(),
                                                 toint(self.flag1a)))
        if self.unknownbits10 is not None:
            items.append('%s\n' % self.unknownbits10.to01())
                         
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        if self.channel_data is not None:
            text += self.channel_data.tostring(indent = indent + 2)
        return text

class PacketAck():
    def __init__(self):
        self.acknr = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        acknrbits, bits = getnbits(14, bits)
        self.acknr = toint(acknrbits)
        return bits

    def tobitarray(self):
        return int2bitarray(self.acknr, 14)

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return ('%s%s (acknr = %d)\n' % (indent_prefix,
                                         self.tobitarray().to01(),
                                         self.acknr))

class Packet():
    def __init__(self):
        self.seqnr = None
        self.parts = []
        self.paddingbits = None

    @debugbits
    def frombitarray(self, bits, state, debug = False):
        original_nbits = len(bits)
        
        seqnr, bits = getnbits(14, bits)
        self.seqnr = toint(seqnr)

        while bits:
            flag1, bits = getnbits(1, bits)
            if flag1 == bitarray('0'):
                part = PacketData()
                self.parts.append(part)
                bits = part.frombitarray(bits, state, debug = debug)
            elif len(bits) >= 14:
                part = PacketAck()
                self.parts.append(part)
                bits = part.frombitarray(bits, debug = debug)
            else:
                # the end
                break

        parsed_nbits = len(self.tobitarray())

        if len(bits) != original_nbits - parsed_nbits:
            raise RuntimeError('Coding error: parsed bits + unparsed bits does not equal total bits: parsed so far: %s' % self.tostring(0))

        nr_of_padding_bits = 8 - (parsed_nbits % 8)
        if len(bits) != nr_of_padding_bits:
            raise ParseError('Left over bits at the end of the packet',
                             bits)

        self.paddingbits, bits = getnbits(nr_of_padding_bits, bits)
        return bits

    def tobitarray(self):
        bits = int2bitarray(self.seqnr, 14)
        for part in self.parts:
            if isinstance(part, PacketData):
                bits.extend('0')
            else:
                bits.extend('1')
            bits.extend(part.tobitarray())
        bits.extend('1')
        if self.paddingbits:
            bits += self.paddingbits
        return bits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        
        databits = self.tobitarray()
        packetbits = bitarray(databits)
        packetbits.fill()
        size = len(packetbits) / 8
        
        text = []
        text.append('%sPacket with size %d\n' % (indent_prefix, size))
        if self.seqnr is not None:
            text.append('%s%s (seqnr = %d)\n' % (indent_prefix,
                                                 int2bitarray(self.seqnr, 14).to01(),
                                                 self.seqnr))

            indent = indent + 14
            
        indent_prefix = ' ' * indent
        for part in self.parts:
            if isinstance(part, PacketData):
                text.append('%s0 (flag1 = 0)\n' % indent_prefix)
            else:
                text.append('%s1 (flag1 = 1)\n' % indent_prefix)
            text.append(part.tostring(indent = indent + 1))

        text.append('%s1 (flag1 = 1)\n' % indent_prefix)
            
        if self.paddingbits:
            text.append('    Bits left over in the last byte: %s\n' % self.paddingbits.to01())
        
        return ''.join(text)

class Parser():
    def __init__(self):
        self.parser_state = ParserState()

    def parsepacket(self, bits, debug = False, exception_on_failure = True):
        packet = Packet()
        bitsleft = None
        errormsg = None
        try:
            packet.frombitarray(bits, self.parser_state, debug = debug)
        except ParseError as e:
            errormsg = str(e)
            bitsleft = e.bitsleft
            if exception_on_failure:
                raise

        if exception_on_failure:
            return packet
        else:
            return packet, bitsleft, errormsg
