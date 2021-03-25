#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

from common.game_items import GamePurchase, GameClass, UnlockableGameClass, \
    UnlockableClassSpecificItem, UnlockableWeapon, UnlockableVoice
from typing import Set, Iterable
import struct
from ipaddress import IPv4Address

REGION_NORTH_AMERICA = 1
REGION_EUROPE = 4
REGION_OCEANIA_AUSTRALIA = 5

TEAM_BLOODEAGLE = 0
TEAM_DIAMONDSWORD = 1
TEAM_SPEC = 255

MESSAGE_PUBLIC = 2
MESSAGE_TEAM = 3
MESSAGE_PRIVATE = 6
MESSAGE_UNKNOWNTYPE = 9
MESSAGE_CONTROL = 12

WATCHNOW_HIREZNEWS = 1
WATCHNOW_TWITCH = 2
WATCHNOW_TRAINING = 3
WATCHNOW_COMMUNITY = 4
WATCHNOW_TICKER = 5

PURCHASE_TYPE_SERVER = 0x01de
PURCHASE_TYPE_BOOSTERS = 0x01fc
PURCHASE_TYPE_NAME = 0x0200
PURCHASE_TYPE_TAG = 0x0221

PURCHASE_ITEM_CHANGE_TAG = 0x000024d1
PURCHASE_ITEM_REMOVE_TAG = 0x000024d2

STDMSG_PLAYER_NOT_FOUND_ONLINE              = 0x0000457b # 'Player @@PLAYER_NAME@@ not found online. Check spelling of player name?'
STDMSG_NAME_HAS_LEFT_AGENCY                 = 0x00004583 # '@@name@@ has left the agency

STDMSG_ALREADY_IN_MATCH_QUEUE               = 0x0000477c # 'You are already in the match queue'
STDMSG_NOT_LEADER_CANT_MANAGE_QUEUE         = 0x00004781 # 'You are not the team leader, only leader can manage the match queue'
STDMSG_JOINED_A_MATCH_QUEUE                 = 0x00004782 # 'You have joined a match queue'
STDMSG_NOT_IN_THE_MATCH_QUEUE               = 0x00004783 # 'You are not in the match queue'
STDMSG_LEFT_MATCH_QUEUE                     = 0x00004783 # 'You have left the match queue'
STDMSG_MISSION_READY_DO_YOU_WANT_TO_JOIN    = 0x00004B72 # 'A mission is ready for you to join, do you want to accept?'
STDMSG_LOGIN_INFO_INVALID                   = 0x00004948 # 'The login information submitted is invalid. Please verify the user name and password.'
STDMSG_LOGIN_IS_VALID                       = 0x00004949 # 'Login is valid'
STDMSG_UNABLE_TO_CONNECT_TO_SERVER          = 0x00004978 # 'Unable to connect to server'
STDMSG_TEST_CONFIRM_POPUP                   = 0x00004b95 # 'Are you sure you would like to test the functionality of the confirm popup?'
STDMSG_PLAYER_ALREADY_MEMBER_OF_YOUR_TEAM   = 0x00004fbd # '@@player_name@@ is already a member of your team.'
STDMSG_PLAYER_ALREADY_MEMBER_OF_OTHER_TEAM  = 0x00004fbe # '@@player_name@@ is a member of another team.'
STDMSG_TEAM_INVITE_SENT_TO_PLAYER           = 0x00004fbf # 'Team invite was sent to @@player_name@@.'
STDMSG_PLAYER_HAS_PENDING_TEAM_INVITE       = 0x00004fc0 # '@@player_name@@ has a pending team invite.'
STDMSG_YOU_ARE_NOT_THE_TEAM_LEADER          = 0x00004fc1 # 'You are not the team leader.'
STDMSG_LEADER_HAS_INVITED_YOU               = 0x00004fc2 # '@@leader_name@@ has invited you to join a team.'
STDMSG_PLAYER_HAS_DECLINED_TEAM_INVITE      = 0x00004fc3 # '@@player_name@@ has declined your team invite.'
STDMSG_TEAM_IS_FULL                         = 0x00004fc6 # 'The team is full.'
STDMSG_PLAYER_IS_NOT_IN_SAME_ALLIANCE       = 0x00004fdd # '@@player_name@@ is not in same alliance.'
STDMSG_TOO_MANY_PENDING_INVITES             = 0x00004fe8 # 'Too many pending invites to send another.'
STDMSG_TEAM_INVITE_EXPIRED                  = 0x00004fea # 'The team invite expired.'

STDMSG_PLAYER_X_ADDED_TO_FRIENDS            = 0x0000a5b6 # '@@PLAYER_NAME@@ added to friends.'
STDMSG_PLAYER_X_REMOVED_FROM_FRIENDS        = 0x0000a5b7 # '@@PLAYER_NAME@@ removed from friends.'
STDMSG_PLAYER_X_IS_BEING_IGNORED            = 0x0000a5b8 # '@@PLAYER_NAME@@ is being ignored.'
STDMSG_PLAYER_X_IS_NO_LONGER_BEING_IGNORED  = 0x0000a5b9 # '@@PLAYER_NAME@@ is no longer being ignored.'
STDMSG_PLAYER_X_IS_ALREADY_YOUR_FRIEND      = 0x0000a5bd # '@@PLAYER_NAME@@ is already your friend.'
STDMSG_PLAYER_X_IS_ALREADY_BLOCKED          = 0x0000a5be # '@@PLAYER_NAME@@ is already blocked.'
STDMSG_PLAYER_X_IS_NOT_ON_YOUR_FRIENDS_LIST = 0x0000a5bf # '@@PLAYER_NAME@@ is not on your friends list.'
STDMSG_PLAYER_X_IS_NOT_ON_YOUR_IGNORE_LIST  = 0x0000a5c0 # '@@PLAYER_NAME@@ is not on your ignore list.'
STDMSG_PLAYER_X_NOT_FOUND                   = 0x0000a5c1 # 'Player @@PLAYER_NAME@@ not found.'
STDMSG_PLAYER_X_IS_FRIEND_CANT_BE_IGNORED   = 0x0000a5c5 # '@@PLAYER_NAME@@ is on your friends list and cannot be ignored.'
STDMSG_PLAYER_X_IS_ON_YOUR_BLOCKED_LIST     = 0x0000a5c6 # '@@PLAYER_NAME@@ is on your Blocked list.'

STDMSG_THAT_NAME_MAY_NOT_BE_USED            = 0x00018ea7 # 'That name may not be used."
STDMSG_THAT_NAME_IS_UNAVAILABLE             = 0x00018ea8 # 'That name is unavailable."

STDMSG_SHOPPING_NOT_AVAILABLE               = 0x00019001 # 'Shopping is not available at this time'
STDMSG_PROBLEM_WITH_YOUR_PURCHASE_REQUEST   = 0x00019002 # 'There was a problem with your purchase request'
STDMSG_PRICE_CHANGE_PLEASE_RETRY            = 0x00019003 # 'There has been a price change, retry purchase if desired'
STDMSG_NOT_ENOUGH_FUNDS                     = 0x00019004 # 'You do not have enough funds to complete the transaction'
STDMSG_MUST_UPGRADE_TO_VIP                  = 0x00019338 # 'You must upgrade your account to VIP Status'
STDMSG_VOTE_BY_X_KICK_PLAYER_X_YES_NO       = 0x0001942F # 'Vote by @@kicker_player_name@@: kick @@player_name@@? (No: F5) (Yes: F6)
STDMSG_PLAYER_X_HAS_BEEN_KICKED             = 0x00019430 # '@@player_name@@ has been kicked'
STDMSG_PLAYER_X_WAS_NOT_VOTED_OUT           = 0x00019431 # '@@player_name@@ was not voted out'
STDMSG_PLAYER_X_NOT_FOUND_IN_MATCH          = 0x00019432 # '@@player_name@@ was not found in your match'
STDMSG_PLAYER_X_MUTED                       = 0x00019440 # '@@PLAYER_NAME@@ muted.'
STDMSG_PLAYER_X_NOT_FOUND                   = 0x00019441 # 'Player @@PLAYER_NAME@@ not found.'
STDMSG_PLAYER_X_NO_LONGER_MUTED             = 0x00019442 # '@@player_name@@ is no longer muted.'
STDMSG_PLAYER_X_IS_NOT_MUTED                = 0x00019444 # 'That player is not muted.'
STDMSG_PLAYER_REPORT_RECEIVED               = 0x000194c6 # 'Player report received.'
STDMSG_PLACED_BACK_IN_QUEUE                 = 0x000194d3 # '@@PLAYER_NAME@@ has left the match lobby. You have been placed back in the queue.'
STDMSG_NO_MORE_VOTEKICKS                    = 0x000194ff # 'You may not initiate any more votekicks.'
STDMSG_PROMOTION_NOT_AVAILABLE              = 0x00019645 # 'This promotion is not available'
STDMSG_NOT_A_VALID_PROMOTION_CODE           = 0x00019646 # 'The code entered is not a valid promotion code'
STDMSG_ITEM_PRICE_HAS_CHANGED               = 0x0001966e # 'Item price has changed'
STDMSG_CANNOT_CONNECT_TO_SERVER             = 0x000197c7 # 'Cannot connect to server. Please wait and try again shortly.'
STDMSG_INCORRECT_PASSWORD                   = 0x00019fdf # 'Incorrect password'

MENU_AREA_SETTINGS = 0x0192C9D3

MENU_AREA_PHYSICS_PRESET_A = 0x0153FCA6
MENU_AREA_PHYSICS_PRESET_B = 0x0153FCA7
MENU_AREA_PHYSICS_PRESET_C = 0x0153FCA8
MENU_AREA_PHYSICS_PRESET_D = 0x0153FCA9
MENU_AREA_PHYSICS_PRESET_E = 0x0153FCAA
MENU_AREA_PHYSICS_PRESET_F = 0x0153FCAB
MENU_AREA_PHYSICS_PRESET_G = 0x0153FCAC

MENU_AREA_LIGHT_LOADOUT_A = 0x02990EE4
MENU_AREA_LIGHT_LOADOUT_B = 0x02990EE5
MENU_AREA_LIGHT_LOADOUT_C = 0x02990EE6
MENU_AREA_LIGHT_LOADOUT_D = 0x02990EE7
MENU_AREA_LIGHT_LOADOUT_E = 0x02990EE8
MENU_AREA_LIGHT_LOADOUT_F = 0x02990EE9
MENU_AREA_LIGHT_LOADOUT_G = 0x02990EEA
MENU_AREA_LIGHT_LOADOUT_H = 0x02990EEB
MENU_AREA_LIGHT_LOADOUT_I = 0x02990EEC

MENU_AREA_HEAVY_LOADOUT_A = 0x02990EED
MENU_AREA_HEAVY_LOADOUT_B = 0x02990EEE
MENU_AREA_HEAVY_LOADOUT_C = 0x02990EEF
MENU_AREA_HEAVY_LOADOUT_D = 0x02990EF0
MENU_AREA_HEAVY_LOADOUT_E = 0x02990EF1
MENU_AREA_HEAVY_LOADOUT_F = 0x02990EF2
MENU_AREA_HEAVY_LOADOUT_G = 0x02990EF3
MENU_AREA_HEAVY_LOADOUT_H = 0x02990EF4
MENU_AREA_HEAVY_LOADOUT_I = 0x02990EF5

MENU_AREA_MEDIUM_LOADOUT_A = 0x02990EF6
MENU_AREA_MEDIUM_LOADOUT_B = 0x02990EF7
MENU_AREA_MEDIUM_LOADOUT_C = 0x02990EF8
MENU_AREA_MEDIUM_LOADOUT_D = 0x02990EF9
MENU_AREA_MEDIUM_LOADOUT_E = 0x02990EFA
MENU_AREA_MEDIUM_LOADOUT_F = 0x02990EFB
MENU_AREA_MEDIUM_LOADOUT_G = 0x02990EFC
MENU_AREA_MEDIUM_LOADOUT_H = 0x02990EFD
MENU_AREA_MEDIUM_LOADOUT_I = 0x02990EFE


class AlreadyLoggedInError(Exception):
    pass


class ParseError(Exception):
    pass


class GameServerConnectedMessage():
    def __init__(self, game_server_id, game_server_ip, game_server_port, game_server_queue):
        self.game_server_id = game_server_id
        self.game_server_ip = game_server_ip
        self.game_server_port = game_server_port
        self.game_server_queue = game_server_queue


class GameServerDisconnectedMessage():
    def __init__(self, game_server_id):
        self.game_server_id = game_server_id


class HttpRequestMessage():
    def __init__(self, peer, env):
        self.peer = peer
        self.env = env


def hexparse(hexstring):
    return bytes([int('0x' + hexbyte, base=16) for hexbyte in hexstring.split()])


def _originalbytes(start, end):
    with open('resources/tribescapture.bin.stripped', 'rb') as f:
        f.seek(start)
        return f.read(end - start)


def findbytype(arr, requestedtype):
    for item in arr:
        if type(item) == requestedtype:
            return item
    return None


# ------------------------------------------------------------
# base types
# ------------------------------------------------------------

class onebyte():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def set(self, value):
        self.value = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<HB', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HB', stream.read(3))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self


class twobytes():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self


class fourbytes():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def set(self, value):
        assert 0 <= value <= 0xFFFFFFFF
        self.value = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<HL', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HL', stream.read(6))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self


class nbytes():
    def __init__(self, ident, valuebytes):
        self.ident = ident
        self.value = valuebytes

    def set(self, value):
        assert len(value) == len(self.value)
        self.value = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<H', self.ident) + self.value)

    def read(self, stream):
        ident = struct.unpack('<H', stream.read(2))[0]
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = stream.read(len(self.value))
        return self


class stringenum():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def set(self, value):
        if not isinstance(value, str):
            raise ValueError('Cannot set the value of a stringenum to %s' % type(value).__name__)
        self.value = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.value)) + self.value.encode('latin1'))

    def read(self, stream):
        ident, length = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = stream.read(length).decode('latin1')
        return self


class arrayofenumblockarrays():
    def __init__(self, ident):
        self.ident = ident
        self.arrays = []
        self.original_bytes = None

    def set(self, arrays):
        self.original_bytes = None
        self.arrays = arrays
        return self

    def set_original_bytes(self, start, end):
        self.original_bytes = (start, end)
        self.arrays = None
        return self

    def write(self, stream):
        if self.original_bytes:
            stream.write(_originalbytes(*self.original_bytes))
        else:
            stream.write(struct.pack('<HH', self.ident, len(self.arrays)))
            for arr in self.arrays:
                stream.write(struct.pack('<H', len(arr)))
                for enumfield in arr:
                    enumfield.write(stream)

    def read(self, stream):
        ident, length1 = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.arrays = []
        for _ in range(length1):
            innerarray = []
            length2 = struct.unpack('<H', stream.read(2))[0]
            for _ in range(length2):
                enumid = struct.unpack('<H', stream.peek(2))[0]
                classname = ('m%04X' % enumid).lower()
                element = globals()[classname]().read(stream)
                innerarray.append(element)
            self.arrays.append(innerarray)
        return self


class enumblockarray():
    def __init__(self, ident):
        self.ident = ident
        self.content = []

    def findbytype(self, requestedtype):
        for item in self.content:
            if type(item) == requestedtype:
                return item
        return None

    def set(self, content):
        self.content = content
        return self

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.content)))
        for el in self.content:
            el.write(stream)

    def read(self, stream):
        ident, length = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.content = []
        for i in range(length):
            enumid = struct.unpack('<H', stream.peek(2))[0]
            classname = ('m%04X' % enumid).lower()
            element = globals()[classname]().read(stream)
            self.content.append(element)
        return self


class variablelengthbytes():
    def __init__(self, ident, content):
        self.ident = ident
        self.content = content

    def set(self, value):
        self.content = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<HL', self.ident, len(self.content)) + self.content)

    def read(self, stream):
        ident, length = struct.unpack('<HL', stream.read(6))
        if ident != self.ident:
            raise ParseError('self.ident(%04X) did not match parsed ident value (%04X)' % (self.ident, ident))
        self.content = stream.read(length)
        return self


class passwordlike(variablelengthbytes):

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.content)) + self.content)

    def read(self, stream):
        ident, length = struct.unpack('<HH', stream.read(4))
        # Length is actually doubled due to server pass's interspersed bytes
        length = (length & 0x7FFF) * 2
        if ident != self.ident:
            raise ParseError('self.ident(%04X) did not match parsed ident value (%04X)' % (self.ident, ident))
        self.content = stream.read(length)
        return self


# ------------------------------------------------------------
# onebyte
# ------------------------------------------------------------

class m0001(onebyte):
    def __init__(self):
        super().__init__(0x0001, 0x00)


class m006f(onebyte):
    def __init__(self):
        super().__init__(0x006f, 0x00)


class m01fa(onebyte):
    def __init__(self):
        super().__init__(0x01fa, 0x00)


class m02c9(onebyte):
    def __init__(self):
        super().__init__(0x02c9, 0x00)


class m0318(onebyte):
    def __init__(self):
        super().__init__(0x0318, 0x00)


class m0326(onebyte):
    def __init__(self):
        super().__init__(0x0326, 0x00)


class m0442(onebyte):
    def __init__(self):
        super().__init__(0x0442, 0x01)

    def set_success(self, success):
        self.value = 1 if success else 0
        return self

class m046b(onebyte):
    def __init__(self):
        super().__init__(0x046b, 0x00)


class m0574(onebyte):
    def __init__(self):
        super().__init__(0x0574, 0x00)


class m0592(onebyte):
    def __init__(self):
        super().__init__(0x0592, 0x00)


class m05d6(onebyte):
    def __init__(self):
        super().__init__(0x05d6, 0x00)


class m05e6(onebyte):
    def __init__(self):
        super().__init__(0x05e6, 0x01)


class m0601(onebyte):
    def __init__(self):
        super().__init__(0x0601, 0x00)


class m063c(onebyte):
    def __init__(self):
        super().__init__(0x063c, 0x00)


class m0673(onebyte):
    def __init__(self):
        super().__init__(0x0673, 0x00)


class m069b(onebyte):
    def __init__(self):
        super().__init__(0x069b, 0x00)


class m069c(onebyte):
    def __init__(self):
        super().__init__(0x069c, 0x00)


class m0703(onebyte):
    def __init__(self):
        super().__init__(0x0703, 0x00)


# ------------------------------------------------------------
# twobytes
# ------------------------------------------------------------

class m0307(twobytes):
    def __init__(self):
        super().__init__(0x0307, 0x0000)


class m053d(twobytes):
    def __init__(self):
        super().__init__(0x053d, 0x0000)


class m0600(twobytes):
    def __init__(self):
        super().__init__(0x0600, 0x0003)


# ------------------------------------------------------------
# fourbytes
# ------------------------------------------------------------

class m0019(fourbytes):
    def __init__(self):
        super().__init__(0x0019, 0x00000000)


class m0035(fourbytes):
    def __init__(self):
        super().__init__(0x0035, 0x00000000)


class m006d(fourbytes):
    def __init__(self):
        super().__init__(0x006d, 0x00000000)


class m0073(fourbytes):
    def __init__(self):
        super().__init__(0x0073, 0x00000000)


class m008b(fourbytes):
    def __init__(self):
        super().__init__(0x008b, 0x00000000)


class m008d(fourbytes):
    def __init__(self):
        super().__init__(0x008d, 0x00000001)


class m0095(fourbytes):
    def __init__(self):
        super().__init__(0x0095, 0x00000000)


class m009d(fourbytes):
    def __init__(self):
        super().__init__(0x009d, 0x00000000)


class m009e(fourbytes):
    def __init__(self):
        super().__init__(0x009e, 0x00000000)


class m00ba(fourbytes):
    def __init__(self):
        super().__init__(0x00ba, 0x00030ce8)


class m00bf(fourbytes):
    def __init__(self):
        super().__init__(0x00bf, 0x00000000)


class m00c3(fourbytes):
    def __init__(self):
        super().__init__(0x00c3, 0x00000000)


class m00c6(fourbytes):
    def __init__(self):
        super().__init__(0x00c6, 0x00000000)


class m00d4(fourbytes):
    def __init__(self):
        super().__init__(0x00d4, 0x00000000)


class m0197(fourbytes):
    def __init__(self):
        super().__init__(0x0197, 0x00000000)


class m01a3(fourbytes):
    def __init__(self):
        super().__init__(0x01a3, 0x00000000)


class m01c0(fourbytes):
    def __init__(self):
        super().__init__(0x01c0, 0x00000000)


class m01c1(fourbytes):
    def __init__(self):
        super().__init__(0x01c1, 0x00000000)


class m01c9(fourbytes):
    def __init__(self):
        super().__init__(0x01c9, 0x00000000)


class m01e3(fourbytes):
    def __init__(self):
        super().__init__(0x01e3, 0x00000000)


class m01e8(fourbytes):
    def __init__(self):
        super().__init__(0x01e8, 0x00000000)


class m020b(fourbytes):
    def __init__(self):
        super().__init__(0x020b, 0x0001994b)


class m020d(fourbytes):
    def __init__(self):
        super().__init__(0x020d, 0x00000000)


class m0219(fourbytes):
    def __init__(self):
        super().__init__(0x0219, 0x00190c0c)


class m021b(fourbytes):
    def __init__(self):
        super().__init__(0x021b, 0x00000000)


class m021f(fourbytes):
    def __init__(self):
        super().__init__(0x021f, 0x00000000)


class m0225(fourbytes):
    def __init__(self):
        super().__init__(0x0225, 0x00067675)


class m0228(fourbytes):
    def __init__(self):
        super().__init__(0x0228, 0x00000000)


class m0242(fourbytes):
    def __init__(self):
        super().__init__(0x0242, 0x00000000)


class m0253(fourbytes):
    def __init__(self):
        super().__init__(0x0253, 0x00000000)


class m0259(fourbytes):
    def __init__(self):
        super().__init__(0x0259, 0x00000000)


class m025a(fourbytes):
    def __init__(self):
        super().__init__(0x025a, 0x00000000)


class m025c(fourbytes):
    def __init__(self):
        super().__init__(0x025c, 0x00000000)


class m025d(fourbytes):
    def __init__(self):
        super().__init__(0x025d, 0x00000000)


class m025e(fourbytes):
    def __init__(self):
        super().__init__(0x025e, 0x00000000)


class m025f(fourbytes):
    def __init__(self):
        super().__init__(0x025f, 0x00000000)


class m0263(fourbytes):
    def __init__(self):
        super().__init__(0x0263, 0x00000000)


class m026d(fourbytes):
    def __init__(self):
        super().__init__(0x026d, 0x00000000)


class m0272(fourbytes):
    def __init__(self):
        super().__init__(0x0272, 0x00000000)


class m0273(fourbytes):
    def __init__(self):
        super().__init__(0x0273, 0x00000000)


class m0296(fourbytes):
    def __init__(self):
        super().__init__(0x0296, 0x00000007)  # player level


class m0298(fourbytes):
    def __init__(self):
        super().__init__(0x0298, 0x00000000)


class m0299(fourbytes):
    def __init__(self):
        super().__init__(0x0299, 0x00000000)


class m02a3(fourbytes):
    def __init__(self):
        super().__init__(0x02a3, 0x00000000)


class m02ab(fourbytes):
    def __init__(self):
        super().__init__(0x02ab, 0x00000000)


class m02ac(fourbytes):
    def __init__(self):
        super().__init__(0x02ac, 0x00000000)


class m02b2(fourbytes):
    def __init__(self):
        super().__init__(0x02b2, 0x00000000)


class m02b3(fourbytes):
    def __init__(self):
        super().__init__(0x02b3, 0x00001d06)


class m02b5(fourbytes):
    def __init__(self):
        super().__init__(0x02b5, 0x00866c82)


class m02b7(fourbytes):
    def __init__(self):
        super().__init__(0x02b7, 0x00000000)


class m02be(fourbytes):
    def __init__(self):
        super().__init__(0x02be, 0x00000000)


class m02c4(fourbytes):
    def __init__(self):
        super().__init__(0x02c4, 0x00000000)


class m02c7(fourbytes):
    def __init__(self):
        super().__init__(0x02c7, 0x00000000)


class m02d6(fourbytes):
    def __init__(self):
        super().__init__(0x02d6, 0x0000001c)


class m02d7(fourbytes):
    def __init__(self):
        super().__init__(0x02d7, 0x0000000E)


class m02d8(fourbytes):
    def __init__(self):
        super().__init__(0x02d8, 0x00000000)


class m02dc(fourbytes):
    def __init__(self):
        super().__init__(0x02dc, 0x00000000)


class m02ea(fourbytes):
    def __init__(self):
        super().__init__(0x02ea, 0x00000000)


class m02ec(fourbytes):
    def __init__(self):
        super().__init__(0x02ec, 0x00000004)


class m02ed(fourbytes):
    def __init__(self):
        super().__init__(0x02ed, 0x00000000)


class m02ef(fourbytes):
    def __init__(self):
        super().__init__(0x02ef, 0x00000000)


class m02f4(fourbytes):
    def __init__(self):
        super().__init__(0x02f4, 0x000000a7)


class m02fc(fourbytes):
    def __init__(self):
        super().__init__(0x02fc, 0x00000000)


class m02ff(fourbytes):
    def __init__(self):
        super().__init__(0x02ff, 0x00000000)


class m0319(fourbytes):
    def __init__(self):
        super().__init__(0x0319, 0x00000000)


class m0320(fourbytes):
    def __init__(self):
        super().__init__(0x0320, 0x00000000)


class m0331(fourbytes):
    def __init__(self):
        super().__init__(0x0331, 0x00000000)


class m0333(fourbytes):
    def __init__(self):
        super().__init__(0x0333, 0x00000000)


class m0343(fourbytes):
    def __init__(self):
        super().__init__(0x0343, 0x00000000)


class m0344(fourbytes):
    def __init__(self):
        super().__init__(0x0344, 0x00000000)


class m0345(fourbytes):
    def __init__(self):
        super().__init__(0x0345, 0x00000096)


class m0346(fourbytes):
    def __init__(self):
        super().__init__(0x0346, 0x0000008c)


class m0347(fourbytes):
    def __init__(self):
        super().__init__(0x0347, 0x00000000)


class m0348(fourbytes):
    def __init__(self):
        super().__init__(0x0348, 0x00000000)


class m035a(fourbytes):
    def __init__(self):
        super().__init__(0x035a, 0x00000000)


class m0363(fourbytes):
    def __init__(self):
        super().__init__(0x0363, 0x00000000)


class m0369(fourbytes):
    def __init__(self):
        super().__init__(0x0369, 0x00000000)


class m036b(fourbytes):
    def __init__(self):
        super().__init__(0x036b, 0x00000000)


class m036c(fourbytes):
    def __init__(self):
        super().__init__(0x036c, 0x00000000)


class m037f(fourbytes):
    def __init__(self):
        super().__init__(0x037f, 0x00000000)


class m0380(fourbytes):
    def __init__(self):
        super().__init__(0x0380, 0x00000000)


class m0385(fourbytes):
    def __init__(self):
        super().__init__(0x0385, 0x00002755)


class m0398(fourbytes):
    def __init__(self):
        super().__init__(0x0398, 0x00000000)


class m03a4(fourbytes):
    def __init__(self):
        super().__init__(0x03a4, 0x00000000)


class m03b4(fourbytes):
    def __init__(self):
        super().__init__(0x03b4, 0x00000000)


class m03ce(fourbytes):
    def __init__(self):
        super().__init__(0x03ce, 0x00000000)


class m03e0(fourbytes):
    def __init__(self):
        super().__init__(0x03e0, 0x00000000)


class m03f1(fourbytes):
    def __init__(self):
        super().__init__(0x03f1, 0x00000000)


class m03f5(fourbytes):
    def __init__(self):
        super().__init__(0x03f5, 0x40000000)


class m03fd(fourbytes):
    def __init__(self):
        super().__init__(0x03fd, 0x00000000)


class m041a(fourbytes):
    def __init__(self):
        super().__init__(0x041a, 0x00000000)


class m042a(fourbytes):
    def __init__(self):
        super().__init__(0x042a, 0x00000000)


class m042b(fourbytes):
    def __init__(self):
        super().__init__(0x042b, 0x00000000)


class m042e(fourbytes):
    def __init__(self):
        super().__init__(0x042e, 0x42700000)


class m042f(fourbytes):
    def __init__(self):
        super().__init__(0x042f, 0x41a00000)


class m0448(fourbytes):
    def __init__(self):
        super().__init__(0x0448, 0x00000000)


class m0452(fourbytes):
    def __init__(self):
        super().__init__(0x0452, 0x00000001)


class m0457(fourbytes):
    def __init__(self):
        super().__init__(0x0457, 0x00000000)


class m0458(fourbytes):
    def __init__(self):
        super().__init__(0x0458, 0x00000000)


class m0472(fourbytes):
    def __init__(self):
        super().__init__(0x0472, 0x00000000)


class m0489(fourbytes):
    def __init__(self):
        super().__init__(0x0489, 0x00000000)


class m049e(fourbytes):
    def __init__(self):
        super().__init__(0x049e, 0x01040B61)


class m04a5(fourbytes):
    def __init__(self):
        super().__init__(0x04a5, 0x00000000)


class m04a6(fourbytes):
    def __init__(self):
        super().__init__(0x04a6, 0x00000000)


class m04a7(fourbytes):
    def __init__(self):
        super().__init__(0x04a7, 0x00000000)


class m04a8(fourbytes):
    def __init__(self):
        super().__init__(0x04a8, 0x00000000)


class m04a9(fourbytes):
    def __init__(self):
        super().__init__(0x04a9, 0x00000000)


class m04aa(fourbytes):
    def __init__(self):
        super().__init__(0x04aa, 0x00000000)


class m04bb(fourbytes):
    def __init__(self):
        super().__init__(0x04bb, 0x00000000)


class m04cb(fourbytes):
    def __init__(self):
        super().__init__(0x04cb, 0x00100000)  # xp


class m04d1(fourbytes):
    def __init__(self):
        super().__init__(0x04d1, 0x00000000)


class m04d5(fourbytes):
    def __init__(self):
        super().__init__(0x04d5, 0x00000000)


class m04d9(fourbytes):
    def __init__(self):
        super().__init__(0x04d9, 0x00000000)


class m04fa(fourbytes):
    def __init__(self):
        super().__init__(0x04fa, 0x00000000)


class m0502(fourbytes):
    def __init__(self):
        super().__init__(0x0502, 0x00000000)


class m0556(fourbytes):
    def __init__(self):
        super().__init__(0x0556, 0x00000000)


class m0558(fourbytes):
    def __init__(self):
        super().__init__(0x0558, 0x00000000)


class m056a(fourbytes):
    def __init__(self):
        super().__init__(0x056a, 0x00000000)


class m0577(fourbytes):
    def __init__(self):
        super().__init__(0x0577, 0x00000000)


class m057d(fourbytes):
    def __init__(self):
        super().__init__(0x057d, 0x00000000)


class m057f(fourbytes):
    def __init__(self):
        super().__init__(0x057f, 0x00000000)


class m058a(fourbytes):
    def __init__(self):
        super().__init__(0x058a, 0x00000000)


class m0591(fourbytes):
    def __init__(self):
        super().__init__(0x0591, 0x00000000)


class m0596(fourbytes):
    def __init__(self):
        super().__init__(0x0596, 0x00000000)


class m0597(fourbytes):
    def __init__(self):
        super().__init__(0x0597, 0x00000000)


class m05b8(fourbytes):
    def __init__(self):
        super().__init__(0x05b8, 0x00000000)


class m05cc(fourbytes):
    def __init__(self):
        super().__init__(0x05cc, 0x00000000)


class m05cf(fourbytes):
    def __init__(self):
        super().__init__(0x05cf, 0x00000000)


class m05d3(fourbytes):
    def __init__(self):
        super().__init__(0x05d3, 0x00001000)  # gold


class m05dc(fourbytes):
    def __init__(self):
        super().__init__(0x05dc, 0x00050000)


class m05e9(fourbytes):
    def __init__(self):
        super().__init__(0x05e9, 0x00000000)


class m05ea(fourbytes):
    def __init__(self):
        super().__init__(0x05ea, 0x00000000)


class m05ee(fourbytes):
    def __init__(self):
        super().__init__(0x05ee, 0x00000000)


class m0602(fourbytes):
    def __init__(self):
        super().__init__(0x0602, 0x00000000)


class m0608(fourbytes):
    def __init__(self):
        super().__init__(0x0608, 0x00000000)


class m060a(fourbytes):
    def __init__(self):
        super().__init__(0x060a, 0x7b19f822)


class m060c(fourbytes):
    def __init__(self):
        super().__init__(0x060c, 0x00000000)


class m0615(fourbytes):
    def __init__(self):
        super().__init__(0x0615, 0x00000000)


class m061d(fourbytes):
    def __init__(self):
        super().__init__(0x061d, 0x00000000)


class m0623(fourbytes):
    def __init__(self):
        super().__init__(0x0623, 0x00000000)


class m062d(fourbytes):
    def __init__(self):
        super().__init__(0x062d, 0x00060001)


class m062e(fourbytes):
    def __init__(self):
        super().__init__(0x062e, 0x00000000)


class m062f(fourbytes):
    def __init__(self):
        super().__init__(0x062f, 0x00000000)


class m0636(fourbytes):
    def __init__(self):
        super().__init__(0x0636, 0x00000000)


class m0637(fourbytes):
    def __init__(self):
        super().__init__(0x0637, 0x00000000)


class m0638(fourbytes):
    def __init__(self):
        super().__init__(0x0638, 0x00000000)


class m0639(fourbytes):
    def __init__(self):
        super().__init__(0x0639, 0x00000000)


class m063a(fourbytes):
    def __init__(self):
        super().__init__(0x063a, 0x00000000)


class m063d(fourbytes):
    def __init__(self):
        super().__init__(0x063d, 0x00000000)


class m065f(fourbytes):
    def __init__(self):
        super().__init__(0x065f, 0x00000000)


class m0660(fourbytes):
    def __init__(self):
        super().__init__(0x0660, 0x00000000)


class m0661(fourbytes):
    def __init__(self):
        super().__init__(0x0661, 0x00000000)


class m0663(fourbytes):
    def __init__(self):
        super().__init__(0x0663, 0x00050001)


class m0664(fourbytes):
    def __init__(self):
        super().__init__(0x0664, 0x00044107)


class m066a(fourbytes):
    def __init__(self):
        super().__init__(0x066a, 0x00000000)


class m0671(fourbytes):
    def __init__(self):
        super().__init__(0x0671, 0x00000000)


class m0672(fourbytes):
    def __init__(self):
        super().__init__(0x0672, 0x00000000)


class m0674(fourbytes):
    def __init__(self):
        super().__init__(0x0674, 0x00000000)


class m0675(fourbytes):
    def __init__(self):
        super().__init__(0x0675, 0x00000000)


class m0676(fourbytes):
    def __init__(self):
        super().__init__(0x0676, 0x00000000)


class m0677(fourbytes):
    def __init__(self):
        super().__init__(0x0677, 0x00000000)


class m067f(fourbytes):
    def __init__(self):
        super().__init__(0x067f, 0x00000000)


class m0680(fourbytes):
    def __init__(self):
        super().__init__(0x0680, 0x00000000)


class m0683(fourbytes):
    def __init__(self):
        super().__init__(0x0683, 0x00000000)


class m0684(fourbytes):
    def __init__(self):
        super().__init__(0x0684, 0x00000000)


class m068c(fourbytes):
    def __init__(self):
        super().__init__(0x068c, 0x00000000)


class m0698(fourbytes):
    def __init__(self):
        super().__init__(0x0698, 0x00000000)


class m0699(fourbytes):
    def __init__(self):
        super().__init__(0x0699, 0x00000000)


class m069d(fourbytes):
    def __init__(self):
        super().__init__(0x069d, 0x00000000)


class m069e(fourbytes):
    def __init__(self):
        super().__init__(0x069e, 0x00000000)


class m069f(fourbytes):
    def __init__(self):
        super().__init__(0x069f, 0x00000000)


class m06b7(fourbytes):
    def __init__(self):
        super().__init__(0x06b7, 0x00000000)


class m06b9(fourbytes):
    def __init__(self):
        super().__init__(0x06b9, 0x00000000)


class m06ba(fourbytes):
    def __init__(self):
        super().__init__(0x06ba, 0x00000000)


class m06bd(fourbytes):
    def __init__(self):
        super().__init__(0x06bd, 0x0000001e)


class m06bf(fourbytes):
    def __init__(self):
        super().__init__(0x06bf, 0x00000032)


class m06c0(fourbytes):
    def __init__(self):
        super().__init__(0x06c0, 0x00000000)


class m06c9(fourbytes):
    def __init__(self):
        super().__init__(0x06c9, 0x00000000)


class m06ea(fourbytes):
    def __init__(self):
        super().__init__(0x06ea, 0x00000000)


class m06ee(fourbytes):
    def __init__(self):
        super().__init__(0x06ee, 0x00000000)


class m06f1(fourbytes):
    def __init__(self):
        super().__init__(0x06f1, 0x41700000)


class m06f5(fourbytes):
    def __init__(self):
        super().__init__(0x06f5, 0x00000000)


class m06fa(fourbytes):
    def __init__(self):
        super().__init__(0x06fa, 0x00000000)


class m0701(fourbytes):
    def __init__(self):
        super().__init__(0x0701, 0x00000000)


class m0704(fourbytes):
    def __init__(self):
        super().__init__(0x0704, 0x00000000)


# ------------------------------------------------------------
# nbytes
# ------------------------------------------------------------
class m0008(nbytes):
    def __init__(self):
        super().__init__(0x0008, hexparse('00 00 00 00 00 00 00 00'))


class m006e(nbytes):
    def __init__(self):
        super().__init__(0x006e, hexparse('00 00 00'))


class m00b7(nbytes):
    def __init__(self):
        super().__init__(0x00b7, hexparse('d0 69 03 1d f9 4c e4 40'))


class m01d7(nbytes):
    def __init__(self):
        super().__init__(0x01d7, hexparse('00 00 00 00 2c 20 e5 40'))


class m01f5(nbytes):
    def __init__(self):
        super().__init__(0x01f5, hexparse('00 00 00 00 00 00 00 00'))


class m0246(nbytes):
    def __init__(self):
        super().__init__(0x0246, hexparse('00 00 00 00 00 00 00 00'))

    def set(self, ip: IPv4Address, port):
        self.value = struct.pack('>BBH', 0x02, 0x00, port) + ip.packed
        return self


class m024f(nbytes):
    def __init__(self):
        super().__init__(0x024f, hexparse('00 00 00 00 00 00 00 00'))

    def set(self, ip: IPv4Address, port: int):
        self.value = struct.pack('>BBH', 0x02, 0x00, port) + ip.packed
        return self


class m0303(nbytes):
    def __init__(self):
        super().__init__(0x0303, hexparse('00 00 00 40 00 00 00 00'))


class m03e3(nbytes):
    def __init__(self):
        super().__init__(0x03e3,
                         hexparse('00 00 00 00 00 00 00 00 '
                                  '00 00 00 00 00 00 00 00'))
        # hexparse('6b 6a 0a 5f 8f 04 e7 41 '
        #         '81 96 29 0b 80 49 83 cf'))


class m0419(nbytes):
    def __init__(self):
        super().__init__(0x0419, hexparse('00 00 00 00 0c 20 e5 40'))


class m0434(nbytes):
    def __init__(self):
        super().__init__(0x0434, hexparse('03 4c ba fa 2e 26 40 01'))


class m04d4(nbytes):
    def __init__(self):
        super().__init__(0x04d4, hexparse('00 00 00 00 00 00 00 00'))


class m05e2(nbytes):
    def __init__(self):
        super().__init__(0x05e2, hexparse('00 00 00 00 00 00 00 00'))


class m057e(nbytes):
    def __init__(self):
        super().__init__(0x057e, hexparse('00 00 00 00 00 00 00 00'))


class m05e2(nbytes):
    def __init__(self):
        super().__init__(0x05e2, hexparse('00 00 00 00 00 00 00 00'))


class m05e4(nbytes):
    def __init__(self):
        super().__init__(0x05e4, hexparse('00 00 00 00 00 00 00 00'))


# ------------------------------------------------------------
# stringenums
# ------------------------------------------------------------

class m0013(stringenum):
    def __init__(self):
        super().__init__(0x0013, 'y')


class m0082(stringenum):
    def __init__(self):
        super().__init__(0x0082, '')


class m00a2(stringenum):
    def __init__(self):
        super().__init__(0x00a2, '')


class m00a3(stringenum):
    def __init__(self):
        super().__init__(0x00a3, '')


class m00aa(stringenum):
    def __init__(self):
        super().__init__(0x00aa, 'y')

    def set_custom(self, custom):
        self.set('y' if custom else 'n')
        return self

class m00ab(stringenum):
    def __init__(self):
        super().__init__(0x00ab, '')


class m01a4(stringenum):
    def __init__(self):
        super().__init__(0x01a4, '')


class m01a6(stringenum):
    def __init__(self):
        super().__init__(0x01a6, 'n')


class m01bc(stringenum):
    def __init__(self):
        super().__init__(0x01bc, 'n')


class m01c4(stringenum):
    def __init__(self):
        super().__init__(0x01c4, 'n')


class m020c(stringenum):
    def __init__(self):
        super().__init__(0x020c, '')


class m021a(stringenum):
    def __init__(self):
        super().__init__(0x021a, '')


class m0261(stringenum):
    def __init__(self):
        super().__init__(0x0261, '')


class m026f(stringenum):
    def __init__(self):
        super().__init__(0x026f, '')


class m02af(stringenum):
    def __init__(self):
        super().__init__(0x02af, 'n')


class m02b1(stringenum):
    def __init__(self):
        super().__init__(0x02b1, '')


class m02b6(stringenum):
    def __init__(self):
        super().__init__(0x02b6, '')


class m02e6(stringenum):
    def __init__(self):
        super().__init__(0x02e6, '')


class m02fe(stringenum):
    def __init__(self):
        super().__init__(0x02fe, '')


class m0300(stringenum):
    def __init__(self):
        super().__init__(0x0300, '')


class m034a(stringenum):
    def __init__(self):
        super().__init__(0x034a, '')


class m035b(stringenum):
    def __init__(self):
        super().__init__(0x035b, 'y')


class m037c(stringenum):
    def __init__(self):
        super().__init__(0x037c, 'n')


class m0437(stringenum):
    def __init__(self):
        super().__init__(0x0437, '')


class m045e(stringenum):
    def __init__(self):
        super().__init__(0x045e, '')


class m0468(stringenum):
    def __init__(self):
        super().__init__(0x0468, 'f8')


class m0494(stringenum):
    def __init__(self):
        super().__init__(0x0494, '')


class m063b(stringenum):
    def __init__(self):
        super().__init__(0x063b, '')


class m0669(stringenum):
    def __init__(self):
        super().__init__(0x0669, '')


class m06b8(stringenum):
    def __init__(self):
        super().__init__(0x06b8, '')


class m06de(stringenum):
    def __init__(self):
        super().__init__(0x06de, '')


class m06e9(stringenum):
    def __init__(self):
        super().__init__(0x06e9, 'n')


class m0705(stringenum):
    def __init__(self):
        super().__init__(0x0705, '')


# ------------------------------------------------------------
# arrayofenumblockarrays
# ------------------------------------------------------------

class m00e9(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x00e9)

    def setservers(self, servers, player_address):
        self.arrays = []
        for server in servers:
            if not server.joinable:
                continue

            self.arrays.append([
                m0385(),
                m06ee(),
                m02c7().set(server.server_id),
                m0008(),
                m02ff(),
                m02ed(),
                m02d8(),
                m02ec(),
                m02d7(),
                m02af(),
                m0013(),
                m00aa(),
                m01a6(),
                m06f1(),
                m0703(),
                m0343().set(len(server.players)),
                m0344(),
                m0259(),
                m03fd(),
                m02b3(),
                m0448().set(server.region),
                m02d6(),
                m06f5(),
                m0299(),
                m0298(),
                m06bf(),
                m069c().set(0x01 if server.password_hash is not None else 0x00),
                m069b().set(0x01 if server.password_hash is not None else 0x00),
                m0300().set(server.game_setting_mode.upper() + ' | ' + server.description),
                m01a4().set(server.motd),
                m02b2().set(server.map_id),
                m02b5(),
                m0347().set(0x00000018),
                m02f4().set(server.get_time_remaining()),
                m0035().set(server.be_score),
                m0197().set(server.ds_score),
                m0246().set(server.address_pair.get_address_seen_from(player_address), server.pingport)
                                                # The value doesn't matter, the client uses the address in a0035
            ])
        return self

    def setplayers(self, players):
        assert len(self.arrays) == 1, 'Can only set players for an m00e9 message that contains a single server'
        self.arrays[0].append(
            m0132().setplayers(players)
        )
        return self

    # Same enum id used for classes as well as servers...
    def setclasses(self, classes: Iterable[GameClass]):
        self.arrays = [
            [
                m0363().set(c.class_id),
                m00a2().set(str(c.secondary_id)),
                m0331(),  # Need to set? Unique between classes?
                m00a3().set(c.family_info_name),
                m00bf(),
                m006d(),  # Need to set?
            ]
            for c
            in classes
        ]

        return self


class m00fe(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x00fe)


class m0116(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0116)


class m0122(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0122)

    def setpurchases(self, purchases: Set[GamePurchase], include_id_mapping: bool):
        return self.set([
            [
                m0013().set('y' if item.shown else 'n'),
                m04d9().set(idx + 1),  # Needs to be unique between items seemingly
                m057f().set(0x27a1),
                # in capture, either 0 or 0x27a1, not clear on pattern; either seems_to work at least for weapon menus?
                m026d().set(item.item_id),
                m04d5(),
                m0273().set(item.item_kind_id),
                m0272(),
                m0380().set(0x0001),
                m05ee(),
                m026f().set(item.name),
                m02ff().set(idx + 1),
                # Needs to be unique between items seemingly; in capture there seems to be a mapping between the value here and other menu sections, unknown if important
                m01a3().set(idx) if isinstance(item, UnlockableVoice) else m01a3(),
                # Voices have this = m02ff's value - 1?
                m03f1(),
                m03a4(),
                m0253(),
                m037f().set(item.category) if isinstance(item, UnlockableWeapon) else m037f(),
                m04bb(),
                m0577(),
                m0398().set(item.game_class.class_id) if isinstance(item, UnlockableClassSpecificItem) or isinstance(
                    item, UnlockableGameClass) else m0398(),
                # Below is used to map weapon name <-> item id; also for weapon upgrades to tie an upgrade to an item id
                m04fa().set(item.item_id) if include_id_mapping else m04fa(),
                m0602(),
                m03fd(),
                # Sometimes filled in capture, may relate to pricing; doesn't seem to cause issues if not filled
                # Price - currently this only handles pricing for items (in gold/xp)
                # Field is also used to handle pricing for gold etc.
                # but that is replayed from capture for now
                m05cb()  # .add_gold_price(0).add_xp_price(0),
            ]
            for idx, item
            in enumerate(purchases)
        ])


class m0127(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0127)

    # 0127 only ever has one element
    def setpurchasedata(self, menu_section: int, purchases: Set[GamePurchase], include_id_mapping: bool):
        return self.set([
            [
                m049e().set(0x0001),
                m02ab().set(menu_section),
                m02ac().set(0x0290),
                m02ff().set(0x000195B5),  # Don't know if this can be 0
                m01a3(),
                m0122().setpurchases(purchases, include_id_mapping),
            ]
        ])


class m0132(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0132)

    def setplayers(self, players):
        player_team_to_datatype_team = {
            None: 1,
            TEAM_SPEC: 1,
            TEAM_BLOODEAGLE: 1,
            TEAM_DIAMONDSWORD: 2
        }

        self.arrays = []
        for player in players:
            self.arrays.append([
                m0348().set(player.unique_id),
                m034a().set(player.display_name),
                m042a(),
                m0558(),
                m0363(),
                m0615(),
                m0452().set(player_team_to_datatype_team[player.team]),
                m0225(),
                m0296(),
                m06ee(),
                m042e(),
                m042f(),
                m03f5()
            ])
        return self


class m0138(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0138)


class m0144(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0144)


class m0148(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0148)


class m05cb(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x05cb)

    def add_gold_price(self, amount):
        self.arrays.append([
            m05cc().set(0x0645),
            m02ff(),
            m035a().set(amount),
            m041a().set(amount),
        ])
        return self

    def add_xp_price(self, amount):
        self.arrays.append([
            m05cc().set(0x27f9),
            m02ff(),
            m035a().set(amount),
            m041a().set(amount),
        ])
        return self

    def add_other_price(self, currency, amount):
        self.arrays.append([
            m05cc().set(currency),
            m02ff(),
            m035a().set(amount),
            m041a().set(amount),
        ])
        return self


class m0632(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0632)


class m0633(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0633)


class m063e(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x063e)


class m0662(arrayofenumblockarrays):
    part1 = [
        [
            m0661().set(0x0191C7D8),
            m01e3().set(0x00002710),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [
            m0661().set(0x0191C7D9),
            m01e3().set(0x00002711),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [
            m0661().set(0x0191C7DA),
            m01e3().set(0x00002712),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [

            m0661().set(0x0191C7DB),
            m01e3().set(0x00002713),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [

            m0661().set(0x0191C7DC),
            m01e3().set(0x00002714),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [

            m0661().set(0x0191C7DD),
            m01e3().set(0x00002715),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [
            m0661().set(0x0191C7DE),
            m01e3().set(0x00002716),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [

            m0661().set(0x0191C7DF),
            m01e3().set(0x00002717),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ],
        [

            m0661().set(0x0191C7E0),
            m01e3().set(0x00002718),
            m065f().set(0x00000001),
            m02fe(),
            m0144()
        ]
    ]
    physics_presets = [
        [
            m0661().set(0x0153FCA6),
            m01e3().set(0x00002710),
            m065f().set(0x0000002A),
            m02fe().set("Standard"),
            m0144().set([
                [
                    m0369().set(0x000005C4),
                    m0261().set("1"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCA7),
            m01e3().set(0x00002711),
            m065f().set(0x0000002A),
            m02fe().set("Accelerate"),
            m0144().set([
                [
                    m0369().set(0x000005AF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B0),
                    m0261().set("150000000"),
                ], [
                    m0369().set(0x000005B1),
                    m0261().set("200000000"),
                ], [
                    m0369().set(0x000005B2),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B3),
                    m0261().set("80000000"),
                ], [
                    m0369().set(0x000005B4),
                    m0261().set("150000000"),
                ], [
                    m0369().set(0x000005B5),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B7),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B8),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B9),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BA),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BB),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BC),
                    m0261().set("150000000"),
                ], [
                    m0369().set(0x000005BD),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BE),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C0),
                    m0261().set("200000000"),
                ], [
                    m0369().set(0x000005C1),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C2),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C3),
                    m0261().set("200000000"),
                ], [
                    m0369().set(0x000005C4),
                    m0261().set("2"),
                ], [
                    m0369().set(0x000005C5),
                    m0261().set("40000000"),
                ], [
                    m0369().set(0x000005C6),
                    m0261().set("30000000"),
                ], [
                    m0369().set(0x000005C7),
                    m0261().set("110000000"),
                ], [
                    m0369().set(0x000005C8),
                    m0261().set("110000000"),
                ], [
                    m0369().set(0x000005C9),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005CA),
                    m0261().set("100000000"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCA8),
            m01e3().set(0x00002712),
            m065f().set(0x0000002A),
            m02fe().set("Impulse"),
            m0144().set([
                [
                    m0369().set(0x000005AF),
                    m0261().set("130000000"),

                ], [
                    m0369().set(0x000005B0),
                    m0261().set("70000000"),

                ], [
                    m0369().set(0x000005B1),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B2),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B3),
                    m0261().set("80000000"),
                ], [
                    m0369().set(0x000005B4),
                    m0261().set("133000000"),
                ], [
                    m0369().set(0x000005B5),
                    m0261().set("153000000"),
                ], [
                    m0369().set(0x000005B6),
                    m0261().set("650000000"),
                ], [
                    m0369().set(0x000005B7),
                    m0261().set("130000000"),
                ], [
                    m0369().set(0x000005B8),
                    m0261().set("20000000"),
                ], [
                    m0369().set(0x000005B9),
                    m0261().set("80000000"),
                ], [
                    m0369().set(0x000005BA),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BB),
                    m0261().set("95000000"),
                ], [
                    m0369().set(0x000005BC),
                    m0261().set("110000000"),
                ], [
                    m0369().set(0x000005BD),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BE),
                    m0261().set("210000000"),
                ], [
                    m0369().set(0x000005BF),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005C0),
                    m0261().set("30000000"),
                ], [
                    m0369().set(0x000005C1),
                    m0261().set("118000000"),
                ], [
                    m0369().set(0x000005C2),
                    m0261().set("320000000"),
                ], [
                    m0369().set(0x000005C3),
                    m0261().set("65000000"),
                ], [
                    m0369().set(0x000005C4),
                    m0261().set("3"),
                ], [
                    m0369().set(0x000005C5),
                    m0261().set("120000000"),
                ], [
                    m0369().set(0x000005C6),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005C7),
                    m0261().set("120000000"),
                ], [
                    m0369().set(0x000005C8),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005C9),
                    m0261().set("140000000"),
                ], [
                    m0369().set(0x000005CA),
                    m0261().set("140000000"),
                ], [
                    m0369().set(0x000005D0),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005D7),
                    m0261().set("0"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCA9),
            m01e3().set(0x00002713),
            m065f().set(0x0000002A),
            m02fe().set("Quake: Ascend"),
            m0144().set([
                [
                    m0369().set(0x000005AF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B0),
                    m0261().set("350000000"),
                ], [
                    m0369().set(0x000005B1),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005B2),
                    m0261().set("260000000"),
                ], [
                    m0369().set(0x000005B3),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B4),
                    m0261().set("350000000"),
                ], [
                    m0369().set(0x000005B5),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B7),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B8),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B9),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BA),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BB),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BC),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BD),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BE),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C0),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C1),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C2),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C3),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C4),
                    m0261().set("4"),
                ], [
                    m0369().set(0x000005C5),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005C6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C7),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005C8),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C9),
                    m0261().set("1000000000"),
                ], [
                    m0369().set(0x000005CA),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D0),
                    m0261().set("1000000000"),
                ], [
                    m0369().set(0x000005D7),
                    m0261().set("100000000"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCAA),
            m01e3().set(0x00002714),
            m065f().set(0x0000002A),
            m02fe().set("Rock Bounce"),
            m0144().set([
                [
                    m0369().set(0x000005C4),
                    m0261().set("5"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCAB),
            m01e3().set(0x00002715),
            m065f().set(0x0000002A),
            m02fe().set("Scramble"),
            m0144().set([
                [
                    m0369().set(0x000005AF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B0),
                    m0261().set("120000000"),
                ], [
                    m0369().set(0x000005B1),
                    m0261().set("200000000"),
                ], [
                    m0369().set(0x000005B2),
                    m0261().set("150000000"),
                ], [
                    m0369().set(0x000005B3),
                    m0261().set("90000000"),
                ], [
                    m0369().set(0x000005B4),
                    m0261().set("90000000"),
                ], [
                    m0369().set(0x000005B5),
                    m0261().set("90000000"),
                ], [
                    m0369().set(0x000005B6),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005B7),
                    m0261().set("200000000"),
                ], [
                    m0369().set(0x000005B8),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005B9),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005BA),
                    m0261().set("500000000"),
                ], [
                    m0369().set(0x000005BB),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BC),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BD),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BE),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BF),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C0),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C1),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C2),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C3),
                    m0261().set("400000000"),
                ], [
                    m0369().set(0x000005C4),
                    m0261().set("6"),
                ], [
                    m0369().set(0x000005C5),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C7),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C8),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005C9),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005CA),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D0),
                    m0261().set("50000000"),
                ], [
                    m0369().set(0x000005D1),
                    m0261().set("140000000"),
                ], [
                    m0369().set(0x000005D2),
                    m0261().set("80000000"),
                ], [
                    m0369().set(0x000005D3),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005D4),
                    m0261().set("120000000"),
                ], [
                    m0369().set(0x000005D5),
                    m0261().set("50000000"),
                ], [
                    m0369().set(0x000005D6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D7),
                    m0261().set("300000000"),
                ]
            ])
        ],
        [
            m0661().set(0x0153FCAC),
            m01e3().set(0x00002716),
            m065f().set(0x0000002A),
            m02fe().set("Freedom"),
            m0144().set([
                [
                    m0369().set(0x000005AF),
                    m0261().set("127000000"),
                ], [
                    m0369().set(0x000005B0),
                    m0261().set("103000000"),
                ], [
                    m0369().set(0x000005B1),
                    m0261().set("121000000"),
                ], [
                    m0369().set(0x000005B2),
                    m0261().set("126000000"),
                ], [
                    m0369().set(0x000005B3),
                    m0261().set("86000000"),
                ], [
                    m0369().set(0x000005B4),
                    m0261().set("108000000"),
                ], [
                    m0369().set(0x000005B5),
                    m0261().set("0"),
                ], [
                    m0369().set(0x000005B6),
                    m0261().set("1537000000"),
                ], [
                    m0369().set(0x000005B7),
                    m0261().set("141000000"),
                ], [
                    m0369().set(0x000005B8),
                    m0261().set("143000000"),
                ], [
                    m0369().set(0x000005B9),
                    m0261().set("119000000"),
                ], [
                    m0369().set(0x000005BA),
                    m0261().set("116000000"),
                ], [
                    m0369().set(0x000005BB),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005BC),
                    m0261().set("117000000"),
                ], [
                    m0369().set(0x000005BD),
                    m0261().set("173000000"),
                ], [
                    m0369().set(0x000005BE),
                    m0261().set("136000000"),
                ], [
                    m0369().set(0x000005BF),
                    m0261().set("164000000"),
                ], [
                    m0369().set(0x000005C0),
                    m0261().set("121000000"),
                ], [
                    m0369().set(0x000005C1),
                    m0261().set("137000000"),
                ], [
                    m0369().set(0x000005C2),
                    m0261().set("194000000"),
                ], [
                    m0369().set(0x000005C3),
                    m0261().set("208000000"),
                ], [
                    m0369().set(0x000005C4),
                    m0261().set("7"),
                ], [
                    m0369().set(0x000005C5),
                    m0261().set("121000000"),
                ], [
                    m0369().set(0x000005C6),
                    m0261().set("331000000"),
                ], [
                    m0369().set(0x000005C7),
                    m0261().set("117000000"),
                ], [
                    m0369().set(0x000005C8),
                    m0261().set("342000000"),
                ], [
                    m0369().set(0x000005C9),
                    m0261().set("126000000"),
                ], [
                    m0369().set(0x000005CA),
                    m0261().set("137000000"),
                ], [
                    m0369().set(0x000005D0),
                    m0261().set("99100000"),
                ], [
                    m0369().set(0x000005D1),
                    m0261().set("108000000"),
                ], [
                    m0369().set(0x000005D2),
                    m0261().set("111000000"),
                ], [
                    m0369().set(0x000005D3),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D4),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D5),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D6),
                    m0261().set("100000000"),
                ], [
                    m0369().set(0x000005D7),
                    m0261().set("100000000")]
            ])
        ]
    ]

    def __init__(self):
        super().__init__(0x0662)
        self.arrays = []
        self.original_bytes = None

    def set(self, loadout_arrays):
        self.arrays = []
        self.arrays.extend(self.part1)
        self.arrays.extend(loadout_arrays)
        self.arrays.extend(self.physics_presets)
        return self

    def setoriginalbytes(self, start, end):
        self.original_bytes = (start, end)
        return self

    def write(self, stream):
        if self.original_bytes:
            stream.write(_originalbytes(*self.original_bytes))
        else:
            super().write(stream)


class m067e(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x067e)


class m0681(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x0681)


class m068b(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x068b)

        region_server_ping_port = 9002

        # Reuse Hirez' UDP echo servers that are set up in each region
        self.arrays = [
            [
                m0448().set(REGION_NORTH_AMERICA),
                m03fd(),
                m06e9(),
                m02ff().set(1),
                m0300().set("North America"),
                m0246().set(IPv4Address('69.147.237.186'), region_server_ping_port)
            ],
            [
                m0448().set(REGION_EUROPE),
                m03fd(),
                m06e9(),
                m02ff().set(2),
                m0300().set("Europe"),
                m0246().set(IPv4Address('95.211.127.133'), region_server_ping_port)
            ],
            [
                m0448().set(REGION_OCEANIA_AUSTRALIA),
                m03fd(),
                m06e9(),
                m02ff().set(3),
                m0300().set("Oceania/Australia"),
                m0246().set(IPv4Address('221.121.148.81'), region_server_ping_port)
            ]
        ]


class m06bb(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x06bb)

        entries = [
            # section, featured, title, url
            [WATCHNOW_TRAINING, True, 'How to join GOTY games', ''],
            [WATCHNOW_TRAINING, True, 'Go to the url mentioned below', ''],
            [WATCHNOW_TRAINING, True, 'http://kfk4ever.com/goty', ''],
            [WATCHNOW_TRAINING, True, 'and just follow the steps.', ''],
            [WATCHNOW_TRAINING, True, '', ''],
            [WATCHNOW_TRAINING, True, 'For help join the discord:', ''],
            [WATCHNOW_TRAINING, True, 'https://discord.gg/8enekHQ', ''],
            [WATCHNOW_TRAINING, True, '', ''],
            [WATCHNOW_TRAINING, True, '', ''],
            [WATCHNOW_TICKER,   True, "Join taserver's discord at https://discord.gg/8enekHQ", ''],
        ]

        for entry_index, entry in enumerate(entries):
            sub_array = [
                m06b7().set(entry_index),
                m06b9().set(entry[0]),
                m02fe().set(entry[2]),
                m06b8().set(entry[3]),
                m06ba().set(entry[1]),
                m0013()
            ]
            self.arrays.append(sub_array)


class m06ef(arrayofenumblockarrays):
    def __init__(self):
        super().__init__(0x06ef)
        self.arrays = [
            [
                m06ee(),
                m042e(),
                m042f(),
                m03f5()
            ],
            [
                m06ee(),
                m042e(),
                m042f(),
                m03f5()
            ]
        ]


# ------------------------------------------------------------
# enumblockarrays
# ------------------------------------------------------------

class a0014(enumblockarray):
    def __init__(self):
        super().__init__(0x0014)

    def setclasses(self, classes: Iterable[GameClass]):
        self.content = [
            m02ab().set(0x000001ed),
            m00e9().setclasses(classes),
        ]
        return self


class a0033(enumblockarray):
    def __init__(self):
        super().__init__(0x0033)


class a0035(enumblockarray):
    def __init__(self):
        super().__init__(0x0035)
        self.content = [
            m0348(),
            m0095(),
            m02be().set(0x0000034f),
            m02b2().set(0x000005A7),
            m02b1().set('TrCTF-ArxNovena'),
            m00a3().set('TribesGame.TrGame_TRCTF'),
            m0326(),
            m0600(),
            m02ff().set(0x000198B1),
            m01a3(),
            m020b().set(0x000198B0),
            m0345(),
            m0346(),
            m02d8()
        ]

    def setmainmenu(self):
        self.findbytype(m02b2).set(0x000005c2)
        self.findbytype(m02be).set(0x00002774)
        self.findbytype(m02b1).set('TribesMainEntry')
        self.findbytype(m00a3).set('TribesGame.TrEntryGame')
        return self

    def setserverdata(self, server, player_address):
        self.content.extend([
            m02c7().set(server.server_id),
            m06ee(),
            m02c4().set(server.match_id),
            m037c(),
            m0452(),
            m0225(),
            m0363(),
            m0615(),
            m06ef(),
            m024f().set(server.address_pair.get_address_seen_from(player_address), server.port),
            m0246().set(server.address_pair.get_address_seen_from(player_address), server.pingport),
            m0448().set(server.region),
            m02b5(),
            m03e0(),
            m0347().set(7),
            m060a()
        ])
        return self


class a003a(enumblockarray):
    def __init__(self):
        super().__init__(0x003a)
        self.content = [
            m049e(),
            m03e3(),
            m0434()
        ]


class a003d(enumblockarray):
    def __init__(self):
        super().__init__(0x003d)

    def set_menu_data(self, class_menu_data):
        ids_to_unlock = [item.item_id for item in class_menu_data.get_every_item() if item.unlocked]

        general_unlocks_arrays = []
        for purchase_index, general_item in enumerate(ids_to_unlock, start=10000):
            general_unlocks_arrays.append([
                m0263().set(purchase_index),
                m026d().set(general_item)
            ])

        general_unlocks_arrays.append([
            m00c6().set(0x00002B76),
            m037f().set(0x00002B76),
            m0263().set(0x10123456),
            m026d().set(0x00001CFE),
            # m05b8(),
            m056a(),
        ])

        skin_unlocks_arrays = [[
            m0095().set(0x00ba8dc7 + idx),
            m0363().set(game_class.class_id),
            m00a2().set(str(game_class.secondary_id)),
            m0138(),
            m02fe(),
            m02b2(),
            m021f(),
            m057d(),
            m057e(),
            m057f().set(0x27a4),
            m05e2(),
            m0684(),
            m05dc(),
            m04cb(),
            m00d4(),
            m025c(),
            m025d(),
            m025e(),
            m025f().set(0xFFFFF448),
            m0596(),
            m0597()
        ]
            for idx, (name, game_class)
            in enumerate(class_menu_data.classes.items())]

        self.content = [
            m03e3(),
            m0348(),
            m0095(),
            m034a().set('Player'),
            m06de().set(''),
            m0303(),
            m0296(),
            m05dc(),
            m04cb(),
            m0701(),
            m05d3(),
            m00d4(),
            m0502(),
            m0448().set(4),
            m05e9(),
            m060c(),
            m05e4(),
            m06ea(),
            m058a(),
            m02be().set(0x00000000),
            m0138().set(general_unlocks_arrays),
            m0662(),
            m0632().set_original_bytes(0x7371, 0x8515),
            m0681().set_original_bytes(0x8822, 0x8898),
            m00fe().set(skin_unlocks_arrays),
            m062d(),
            m008d(),
            m062e(),
            m0419(),
            m01d7(),
            m00b7(),
            m062f(),
            m01bc(),
            m0468(),
            m0663(),
            m068b(),
            m0681().set_original_bytes(0x8822, 0x8898)]

        return self

    def set_player(self, player):
        self.findbytype(m0348).set(player.unique_id)
        self.findbytype(m034a).set(player.display_name)
        self.findbytype(m06de).set(player.player_settings.clan_tag)
        self.findbytype(m05dc).set(player.player_settings.progression.rank_xp)

        loadout_arrays = []
        loadout_overall_idx = 0
        for class_id, class_loadout in player.get_unmodded_loadouts().get_data().items():
            for loadout_index, loadout in class_loadout.items():
                loadout_id = player.get_unmodded_loadouts().loadout_key2id[(class_id, loadout_index)]

                entry_array = []
                for slot, equipment in loadout.items():
                    if isinstance(equipment, str):
                        equip_field = m0437().set(equipment)
                    else:
                        equip_field = m0261().set(str(equipment))
                    entry_array.append([
                        m0369().set(slot),
                        equip_field
                    ])
                entry_array.append([
                    m0369().set(0x00000442),
                    m0261().set(str(8167))
                ])
                entry_array.append([
                    m0369().set(0x00000443),
                    m0261().set(str(8162))
                ])
                entry_array.append([
                    m0369().set(0x00000447),
                    m0261().set(str(class_id))
                ])
                if loadout_index:
                    entry_array.append([
                        m0369().set(0x0000053C),
                        m0261().set(str(loadout_index))
                    ])

                loadout_arrays.append([
                    m0661().set(loadout_id),
                    m01e3().set(loadout_overall_idx),
                    m065f().set(0x00000001),
                    m02fe().set(""),
                    m0144().set(entry_array)
                ])
                loadout_overall_idx += 1

        self.findbytype(m0662).set(loadout_arrays)

        return self


class a0041(enumblockarray):
    def __init__(self):
        super().__init__(0x0041)


class a004c(enumblockarray):
    def __init__(self):
        super().__init__(0x004c)


class a006d(enumblockarray):
    def __init__(self):
        super().__init__(0x006d)


class a006f(enumblockarray):
    def __init__(self):
        super().__init__(0x006f)
        self.content = [
            m00e9()
        ]


class a0070(enumblockarray):
    def __init__(self):
        super().__init__(0x0070)
        self.content = [
            m009e(),
            m02e6(),
            m02fe(),
            m06de()
        ]


class a0085(enumblockarray):
    def __init__(self):
        super().__init__(0x0085)


class a00b0(enumblockarray):
    def __init__(self):
        super().__init__(0x00b0)
        self.content = [
            m035b(),
            m0348(),
            m042a(),
            m0558(),
            m02c7(),
            m0333()
        ]

    def setlength(self, length):
        if length == 9:
            self.content.extend([
                m02ff(),
                m06ee(),
                m042b().set(STDMSG_JOINED_A_MATCH_QUEUE)
            ])
        else:
            self.content.extend([
                m02c4(),
                m06ee(),
                m0452(),
                m0225()
            ])
        return self

    def set_server(self, server):
        server_id = self.findbytype(m02c7)
        if server_id:
            server_id.set(server.server_id)

        match_id = self.findbytype(m02c4)
        if match_id:
            match_id.set(server.match_id)

        return self

    def set_player(self, player_id):
        self.findbytype(m0348).set(player_id)
        return self


class a00b1(enumblockarray):
    def __init__(self):
        super().__init__(0x00b1)


class a00b2(enumblockarray):
    def __init__(self):
        super().__init__(0x00b2)


class a00b3(enumblockarray):
    def __init__(self):
        super().__init__(0x00b3)


class a00b4(enumblockarray):
    def __init__(self):
        super().__init__(0x00b4)
        self.content = [
            m042b().set(STDMSG_MISSION_READY_DO_YOU_WANT_TO_JOIN),
            m01c4(),
            m0556(),
            m035b(),
            m0348(),
            m042a(),
            m0558(),
            m02c7(),
            m0333(),
            m06bd(),
            m02c4(),
            m06ee(),
            m0452(),
            m0225()
        ]

    def set_server(self, server):
        server_id = self.findbytype(m02c7)
        if server_id:
            server_id.set(server.server_id)

        match_id = self.findbytype(m02c4)
        if match_id:
            match_id.set(server.match_id)

        return self

    def set_player(self, player_id):
        self.findbytype(m0348).set(player_id)
        return self


class a00d5(enumblockarray):
    def __init__(self):
        super().__init__(0x00d5)
        self.content = [
            m0228().set(2),
            m00e9(),
            m0347().set(0x2f6b9f)
        ]

    def setservers(self, servers, player_address):
        self.findbytype(m00e9).setservers(servers, player_address)
        return self


class a00ec(enumblockarray):
    def __init__(self):
        super().__init__(0x00ec)


class a00fb(enumblockarray):
    def __init__(self):
        super().__init__(0x00fb)


class a010f(enumblockarray):
    def __init__(self):
        super().__init__(0x010f)


class a011b(enumblockarray):
    def __init__(self):
        super().__init__(0x011b)


class a011c(enumblockarray):
    def __init__(self):
        super().__init__(0x011c)


class a0145(enumblockarray):
    def __init__(self):
        super().__init__(0x0145)


class a0175(enumblockarray):
    def __init__(self):
        super().__init__(0x0175)
        self.content = [
            m0442(),
            m02fc(),
            m05cf(),
            m02ab(),
            m04d9(),
            m05cc(),
            m035a(),
            m0683(),
            m0669(),
            m049e()
        ]


class a0176(enumblockarray):
    def __init__(self):
        super().__init__(0x0176)


class a0177(enumblockarray):
    def __init__(self):
        super().__init__(0x0177)

    def setdata(self, menu_part: int, purchase_data: Set[GamePurchase], include_id_mapping: bool):
        return self.set([
            m02ab().set(menu_part),
            m0127().setpurchasedata(menu_part, purchase_data, include_id_mapping),
            m049e().set(0x0001),
            m0442().set_success(True),
        ])


class a0182(enumblockarray):
    def __init__(self):
        super().__init__(0x0182)


class a0183(enumblockarray):
    def __init__(self):
        super().__init__(0x0183)


class a018a(enumblockarray):
    def __init__(self):
        super().__init__(0x018a)


class a018b(enumblockarray):
    def __init__(self):
        super().__init__(0x018b)


class a018c(enumblockarray):
    def __init__(self):
        super().__init__(0x018c)


class a0197(enumblockarray):
    def __init__(self):
        super().__init__(0x0197)
        self.content = [
            m0664(),
            m03e3(),
            m03e0()
        ]


class a019a(enumblockarray):
    def __init__(self):
        super().__init__(0x019a)


class a01a2(enumblockarray):
    def __init__(self):
        super().__init__(0x01a2)


class a01a4(enumblockarray):
    def __init__(self):
        super().__init__(0x01a4)


class a01a5(enumblockarray):
    def __init__(self):
        super().__init__(0x01a5)


class a01b5(enumblockarray):
    def __init__(self):
        super().__init__(0x01b5)

    def add_watch_now_menu(self):
        self.content = [
            m06bb()
        ]
        return self


class a01bc(enumblockarray):
    def __init__(self):
        super().__init__(0x01bc)
        self.content = [
            m049e(),
            m0489().set(0x0000000c),
            m0319()
        ]


class a01c6(enumblockarray):
    def __init__(self):
        super().__init__(0x01c6)


class a01c8(enumblockarray):
    def __init__(self):
        super().__init__(0x01c8)


# ------------------------------------------------------------
# special fields
# ------------------------------------------------------------

# Player password
class m0056(variablelengthbytes):
    def __init__(self):
        super().__init__(0x0056, b'0' * 90)

    def read(self, stream):
        super().read(stream)
        if len(self.content) < 72:
            raise ParseError('self.content is not allowed to be shorter than 72 bytes')
        return self


# Server password
class m032e(passwordlike):
    def __init__(self):
        super().__init__(0x032e, b'0')


class m0620(passwordlike):
    def __init__(self):
        super().__init__(0x0620, b'0')


class originalfragment():
    def __init__(self, fromoffset, tooffset):
        self.fromoffset = fromoffset
        self.tooffset = tooffset

    def write(self, stream):
        stream.write(_originalbytes(self.fromoffset, self.tooffset))


def construct_top_level_enumfield(stream):
    ident = struct.unpack('<H', stream.peek(2))[0]
    classname = ('a%04X' % ident).lower()

    if classname not in globals():
        classname = ('m%04X' % ident).lower()

    obj = globals()[classname]().read(stream)
    return obj
