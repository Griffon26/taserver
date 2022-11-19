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
import struct
import datetime
from typing import Optional, List

# These IDs should only be extended, not changed, to allow for some
# backward compatibility

_MSGID_LOGIN2LAUNCHER_NEXTMAP = 0x1000
_MSGID_LOGIN2LAUNCHER_SETPLAYERLOADOUTS = 0x1001
_MSGID_LOGIN2LAUNCHER_REMOVEPLAYERLOADOUTS = 0x1002
_MSGID_LOGIN2LAUNCHER_PROTOCOL_VERSION = 0x1003
_MSGID_LOGIN2LAUNCHER_ADD_PLAYER = 0x1004
_MSGID_LOGIN2LAUNCHER_REMOVE_PLAYER = 0x1005
_MSGID_LOGIN2LAUNCHER_PINGS = 0x1006
_MSGID_LOGIN2LAUNCHER_MAPVOTERESULT = 0x1007

_MSGID_LAUNCHER2LOGIN_SERVERINFO = 0x2000
_MSGID_LAUNCHER2LOGIN_MAPINFO = 0x2001
_MSGID_LAUNCHER2LOGIN_TEAMINFO = 0x2002
_MSGID_LAUNCHER2LOGIN_SCOREINFO = 0x2003
_MSGID_LAUNCHER2LOGIN_MATCHTIME = 0x2004
_MSGID_LAUNCHER2LOGIN_MATCHEND = 0x2005
_MSGID_LAUNCHER2LOGIN_PROTOCOL_VERSION = 0x2006
_MSGID_LAUNCHER2LOGIN_SERVERREADY = 0x2007
_MSGID_LAUNCHER2LOGIN_ADDRESSINFO = 0x2008
_MSGID_LAUNCHER2LOGIN_WAITING_FOR_MAP = 0x2009

_MSGID_GAME2LAUNCHER_PROTOCOL_VERSION = 0x3000
_MSGID_GAME2LAUNCHER_TEAMINFO = 0x3001
_MSGID_GAME2LAUNCHER_SCOREINFO = 0x3002
_MSGID_GAME2LAUNCHER_MATCHTIME = 0x3003
_MSGID_GAME2LAUNCHER_MATCHEND = 0x3004
_MSGID_GAME2LAUNCHER_LOADOUTREQUEST = 0x3005
_MSGID_GAME2LAUNCHER_MAPINFO = 0x3006
_MSGID_GAME2LAUNCHER_SERVERINFO = 0x3007

_MSGID_LAUNCHER2GAME_LOADOUT = 0x4000
_MSGID_LAUNCHER2GAME_NEXTMAP = 0x4001
_MSGID_LAUNCHER2GAME_PINGS = 0x4002
_MSGID_LAUNCHER2GAME_INIT = 0x4003
_MSGID_LAUNCHER2GAME_PLAYER_INFO = 0x4004

_MSGID_CLIENT2LOGIN_CONNECT = 0x5000
_MSGID_CLIENT2LOGIN_SWITCHMODE = 0x5001
_MSGID_CLIENT2LOGIN_LOADOUTCHANGE = 0x5002

_MSGID_LOGIN2CLIENT_MODEINFO = 0x6000
_MSGID_LOGIN2CLIENT_MENUDATA = 0x6001
_MSGID_LOGIN2CLIENT_LOADOUTS = 0x6002

_MSGID_AUTH2LOGIN_AUTHCODE_REQUEST = 0x7000
_MSGID_AUTH2LOGIN_REGISTER_AS_BOT = 0x7001
_MSGID_AUTH2LOGIN_CHAT = 0x7002
_MSGID_AUTH2LOGIN_SET_EMAIL = 0x7003

_MSGID_LOGIN2AUTH_AUTHCODE_RESULT = 0x8000
_MSGID_LOGIN2AUTH_CHAT_MESSAGE = 0x8001


class Message:
    def to_bytes(self):
        return struct.pack('<H', self.msg_id) + bytes(json.dumps(self.__dict__), encoding='utf8')

    def to_string(self):
        return json.dumps({'msg_id': self.msg_id, **self.__dict__})

    @classmethod
    def from_bytes(cls, data):
        msg_id = struct.unpack('<H', data[0:2])[0]
        if msg_id != cls.msg_id:
            raise ValueError('Cannot parse object of this type from these bytes')

        members = json.loads(data[2:])
        return cls(**members)

    @classmethod
    def from_dict(cls, members):
        if members['msg_id'] != cls.msg_id:
            raise ValueError('Cannot parse object of this type from this json')
        del members['msg_id']
        return cls(**members)


class Login2LauncherNextMapMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_NEXTMAP


class Login2LauncherSetPlayerLoadoutsMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_SETPLAYERLOADOUTS

    def __init__(self, unique_id, loadouts):
        self.unique_id = unique_id
        self.loadouts = loadouts


class Login2LauncherRemovePlayerLoadoutsMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_REMOVEPLAYERLOADOUTS

    def __init__(self, unique_id):
        self.unique_id = unique_id


# Example json: { 'version' : '0.1.0' }
class Login2LauncherProtocolVersionMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_PROTOCOL_VERSION

    def __init__(self, version: str):
        self.version = version


# Example json: { 'unique_id' : 123, 'display_name': 'playername' 'ip' : '1.2.3.4', 'eligible_for_first_win': false }
class Login2LauncherAddPlayer(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_ADD_PLAYER

    def __init__(self, unique_id: int, display_name: str, ip: str, rank_xp: int, eligible_for_first_win: bool):
        self.unique_id = unique_id
        self.display_name = display_name
        self.ip = ip
        self.rank_xp = rank_xp
        self.eligible_for_first_win = eligible_for_first_win


# Example json: { 'unique_id' : 123, 'ip' : '1.2.3.4' }
class Login2LauncherRemovePlayer(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_REMOVE_PLAYER

    def __init__(self, unique_id: int, ip: str):
        self.unique_id = unique_id
        self.ip = ip


# Example json: { 'player_pings': { '123': 10, '124': 25 } }
class Login2LauncherPings(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_PINGS

    def __init__(self, player_pings):
        self.player_pings = player_pings


# Example json: { 'map_id': 2 }
class Login2LauncherMapVoteResult(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_MAPVOTERESULT

    def __init__(self, map_id: Optional[int]):
        self.map_id = map_id


# Example json: { 'description' : 'some server',
#                 'motd' : 'message of the day',
#                 'game_setting_mode' : 'goty',
#                 'password_hash' : [ 1, 2, 3, 4 ] or None }
class Launcher2LoginServerInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_SERVERINFO

    def __init__(self, description: str, motd: str,
                 game_setting_mode: str, password_hash: Optional[List[int]]):
        self.description = description
        self.motd = motd
        self.game_setting_mode = game_setting_mode
        self.password_hash = password_hash


class Launcher2LoginMapInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MAPINFO

    def __init__(self, map_id):
        self.map_id = map_id


class Launcher2LoginTeamInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_TEAMINFO

    def __init__(self, player_to_team_id):
        self.player_to_team_id = player_to_team_id


class Launcher2LoginScoreInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_SCOREINFO

    def __init__(self, be_score, ds_score):
        self.be_score = be_score
        self.ds_score = ds_score


class Launcher2LoginMatchTimeMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MATCHTIME

    def __init__(self, seconds_remaining: int, counting: bool):
        self.seconds_remaining = seconds_remaining
        self.counting = counting


# Example json: { 'votable_maps' : [ "TrCTF-Katabatic", "TrCTF-ArxNovena" ],
#                 'players_time_played' : {
#                    '123': { 'time': 234, 'win': True }
#                 }
#               }
class Launcher2LoginMatchEndMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MATCHEND

    def __init__(self, next_map_idx, votable_maps: List[str], players_time_played):
        self.next_map_idx = next_map_idx
        self.votable_maps = votable_maps
        self.players_time_played = players_time_played


class Launcher2LoginAddressInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_ADDRESSINFO

    def __init__(self, external_ip: str, internal_ip: str):
        self.external_ip = external_ip
        self.internal_ip = internal_ip


# Example json: { 'version' : '0.1.0' }
class Launcher2LoginProtocolVersionMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_PROTOCOL_VERSION

    def __init__(self, version: str):
        self.version = version


# Example json: { 'port' : 7777, 'pingport' : 9002 }
class Launcher2LoginServerReadyMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_SERVERREADY

    def __init__(self, port: Optional[int], pingport: Optional[int]):
        self.port = port
        self.pingport = pingport


class Launcher2LoginWaitingForMap(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_WAITING_FOR_MAP

    def __init__(self):
        pass


# Example json: { 'version' : '0.1.0' }
class Game2LauncherProtocolVersionMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_PROTOCOL_VERSION

    def __init__(self, version: str):
        self.version = version


# Example json: { 'description' : 'some server',
#                 'motd' : 'message of the day',
#                 'game_setting_mode' : 'goty',
#                 'password_hash' : [ 1, 2, 3, 4 ] or None }
class Game2LauncherServerInfoMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_SERVERINFO

    def __init__(self, description: str, motd: str,
                 game_setting_mode: str, password_hash: Optional[List[int]]):
        self.description = description
        self.motd = motd
        self.game_setting_mode = game_setting_mode
        self.password_hash = password_hash


# Example json: { 'map_id' : 1447 }
# Where: 1447 (0x5a7) is the map ID of Katabatic
class Game2LauncherMapInfoMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_MAPINFO

    def __init__(self, map_id: int):
        self.map_id = map_id


# Example json: { 'player_to_team_id' : { '123' : 0, '234' : 1, '321' : 255 } }
# Where: 0 = BE, 1 = DS, 255 = spec and the other values are player's unique_id
class Game2LauncherTeamInfoMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_TEAMINFO

    def __init__(self, player_to_team_id):
        self.player_to_team_id = player_to_team_id


# Example json: { 'be_score' : 1, 'ds_score' : 5 }
class Game2LauncherScoreInfoMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_SCOREINFO

    def __init__(self, be_score, ds_score):
        self.be_score = be_score
        self.ds_score = ds_score


# Example json: { 'seconds_remaining' : 60, 'counting' : true }
# Where 'counting' indicates if the time is counting down or the countdown is frozen
class Game2LauncherMatchTimeMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_MATCHTIME

    def __init__(self, seconds_remaining: int, counting: bool):
        self.seconds_remaining = seconds_remaining
        self.counting = counting


# Example json: {
#                  'controller_context' : opaque_json_structure,
#                  'votable_maps' : [ "TrCTF-Katabatic", "TrCTF-ArxNovena" ],
#                  'next_map_wait_time': 30,
#                  'players_time_played': {
#                      '5': { 'time': 350, 'win': true },
#                      '1000002': { 'time': 183, 'win': false }
#                  },
#               }
# Where 'opaque_json_structure' is a structure chosen by the controller and that will
#       be passed to the next controller instance after map change
class Game2LauncherMatchEndMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_MATCHEND

    def __init__(self, controller_context, votable_maps, players_time_played, next_map_wait_time: int):
        self.controller_context = controller_context
        self.votable_maps = votable_maps
        self.players_time_played = players_time_played
        self.next_map_wait_time = next_map_wait_time


# Example json: { 'player_unique_id' : 123, 'class_id' : 1683, 'loadout_number' : 0 }
# Where:
#   'class_id' 1683 = LIGHT_CLASS, 1693 = MEDIUM_CLASS, 1692 = HEAVY_CLASS
#   'loadout_number' is in the range [0, 8]
class Game2LauncherLoadoutRequest(Message):
    msg_id = _MSGID_GAME2LAUNCHER_LOADOUTREQUEST

    def __init__(self, player_unique_id: int, class_id: int, loadout_number: int):
        self.player_unique_id = player_unique_id
        self.class_id = class_id
        self.loadout_number = loadout_number


# Example json: { 'player_unique_id' : 123,
#                 'class_id' : 1683,
#                 'loadout' : { '1086' : 7401,
#                               '1087' : 7401,
#                               '1765' : 7401,
#                               '1088' : 7832,
#                               '1089' : 7434,
#                               '1093' : 7834,
#                               '1094' : 8667 } }
# Where:
#   'class_id':
#       1683 = LIGHT_CLASS
#       1693 = MEDIUM_CLASS
#       1692 = HEAVY_CLASS
#   'loadout':
#       1086 = SLOT_PRIMARY_WEAPON
#       1087 = SLOT_SECONDARY_WEAPON
#       1765 = SLOT_TERTIARY_WEAPON
#       1088 = SLOT_PACK
#       1089 = SLOT_BELT
#       1093 = SLOT_SKIN
#       1094 = SLOT_VOICE
#       7401, ... = EQUIPMENT_SPINFUSOR, ...
class Launcher2GameLoadoutMessage(Message):
    msg_id = _MSGID_LAUNCHER2GAME_LOADOUT

    def __init__(self, player_unique_id, class_id, loadout):
        self.player_unique_id = player_unique_id
        self.class_id = class_id
        self.loadout = loadout


# Example json: {}
class Launcher2GameNextMapMessage(Message):
    msg_id = _MSGID_LAUNCHER2GAME_NEXTMAP

    def __init__(self):
        pass


# Example json: { 'player_pings': { '123': 10, '124': 25 } }
class Launcher2GamePings(Message):
    msg_id = _MSGID_LAUNCHER2GAME_PINGS

    def __init__(self, player_pings):
        self.player_pings = player_pings


# Example json: { 'player_unique_id' : 123456, 'rank_xp': 1234567, 'eligible_for_first_win': false }
class Launcher2GamePlayerInfo(Message):
    msg_id = _MSGID_LAUNCHER2GAME_PLAYER_INFO

    def __init__(self, player_unique_id: int, rank_xp: int, eligible_for_first_win: bool):
        self.player_unique_id = player_unique_id
        self.rank_xp = rank_xp
        self.eligible_for_first_win = eligible_for_first_win


# Example json: { 'controller_context': opaque_json_structure }
# Where: opaque_json_structure is the same data that the controller passed as parameter of the match end message.
#        This allows the controller to communicate state to another instance of itself. The first controller
#        instance will receive an empty structure {}
class Launcher2GameInit(Message):
    msg_id = _MSGID_LAUNCHER2GAME_INIT

    def __init__(self, controller_context):
        self.controller_context = controller_context


class Client2LoginConnect(Message):
    msg_id = _MSGID_CLIENT2LOGIN_CONNECT


class Client2LoginSwitchMode(Message):
    msg_id = _MSGID_CLIENT2LOGIN_SWITCHMODE


class Client2LoginLoadoutChange(Message):
    msg_id = _MSGID_CLIENT2LOGIN_LOADOUTCHANGE

    def __init__(self, game_class, loadout_index, loadout_slot, value):
        self.game_class = game_class
        self.loadout_index = loadout_index
        self.loadout_slot = loadout_slot
        self.value = value


class Login2ClientModeInfo(Message):
    msg_id = _MSGID_LOGIN2CLIENT_MODEINFO

    def __init__(self, game_setting_mode: str):
        self.game_setting_mode = game_setting_mode


class Login2ClientMenuData(Message):
    msg_id = _MSGID_LOGIN2CLIENT_MENUDATA

    def __init__(self, menu_item, timestamp_value: datetime.datetime):
        self.menu_item = menu_item
        self.timestamp = timestamp_value.isoformat()


class Login2ClientLoadouts(Message):
    msg_id = _MSGID_LOGIN2CLIENT_LOADOUTS

    def __init__(self, loadout_item):
        self.loadout_item = loadout_item


# The source is an arbitrary string that will be sent back together with the AuthCodeResult to allow the handler
# to forward the result to the originator of the request (on hirez or on community server).
# Example json: { 'source': 'hirez', 'login_name': 'Griffon26', 'email_address': 'griffon26@kfk4ever.com' }
class Auth2LoginAuthCodeRequestMessage(Message):
    msg_id = _MSGID_AUTH2LOGIN_AUTHCODE_REQUEST

    def __init__(self, source: str, login_name: str, email_address: str):
        self.source = source
        self.login_name = login_name
        self.email_address = email_address


# Example json: { }
class Auth2LoginRegisterAsBotMessage(Message):
    msg_id = _MSGID_AUTH2LOGIN_REGISTER_AS_BOT


# Example json: { 'login_name': 'Griffon26', 'text': 'Hey there!' }
class Auth2LoginChatMessage(Message):
    msg_id = _MSGID_AUTH2LOGIN_CHAT

    def __init__(self, login_name, text):
        self.login_name = login_name
        self.text = text


class Auth2LoginSetEmailMessage(Message):
    msg_id = _MSGID_AUTH2LOGIN_SET_EMAIL

    def __init__(self, login_name: str, email_address: str):
        self.login_name = login_name
        self.email_address = email_address


# If authentication failed then authcode will be None
# Example json: { 'source': 'hirez', 'login_name': 'Griffon26', 'email_address': 'griffon26@kfk4ever.com',
#                 'authcode': 'someauthcode', 'clarification': 'This account is not available' }
class Login2AuthAuthCodeResultMessage(Message):
    msg_id = _MSGID_LOGIN2AUTH_AUTHCODE_RESULT

    def __init__(self, source: str, login_name: str, email_address: str,
                 authcode: Optional[str], error_message: Optional[str]):
        self.source = source
        self.login_name = login_name
        self.email_address = email_address
        self.authcode = authcode
        self.error_message = error_message


# Example json: { 'login_name': 'Griffon26', 'text': 'Hey there!' }
class Login2AuthChatMessage(Message):
    msg_id = _MSGID_LOGIN2AUTH_CHAT_MESSAGE

    def __init__(self, login_name: str, verified: bool, text: str):
        self.login_name = login_name
        self.verified = verified
        self.text = text


_message_classes = [

    Login2LauncherProtocolVersionMessage,
    Login2LauncherNextMapMessage,
    Login2LauncherSetPlayerLoadoutsMessage,
    Login2LauncherRemovePlayerLoadoutsMessage,
    Login2LauncherAddPlayer,
    Login2LauncherRemovePlayer,
    Login2LauncherPings,
    Login2LauncherMapVoteResult,

    Launcher2LoginServerInfoMessage,
    Launcher2LoginMapInfoMessage,
    Launcher2LoginTeamInfoMessage,
    Launcher2LoginScoreInfoMessage,
    Launcher2LoginMatchTimeMessage,
    Launcher2LoginMatchEndMessage,
    Launcher2LoginProtocolVersionMessage,
    Launcher2LoginServerReadyMessage,
    Launcher2LoginAddressInfoMessage,
    Launcher2LoginWaitingForMap,

    Game2LauncherProtocolVersionMessage,
    Game2LauncherServerInfoMessage,
    Game2LauncherMapInfoMessage,
    Game2LauncherTeamInfoMessage,
    Game2LauncherScoreInfoMessage,
    Game2LauncherMatchTimeMessage,
    Game2LauncherMatchEndMessage,
    Game2LauncherLoadoutRequest,

    Launcher2GameLoadoutMessage,
    Launcher2GameNextMapMessage,
    Launcher2GamePings,
    Launcher2GameInit,
    Launcher2GamePlayerInfo,

    Client2LoginConnect,
    Client2LoginSwitchMode,
    Client2LoginLoadoutChange,

    Login2ClientModeInfo,
    Login2ClientMenuData,
    Login2ClientLoadouts,

    Auth2LoginAuthCodeRequestMessage,
    Auth2LoginRegisterAsBotMessage,
    Auth2LoginChatMessage,
    Auth2LoginSetEmailMessage,

    Login2AuthAuthCodeResultMessage,
    Login2AuthChatMessage
]

_message_map = {msg_class.msg_id: msg_class for msg_class in _message_classes}


def parse_message_from_bytes(message_bytes):
    msg_id = struct.unpack('<H', message_bytes[0:2])[0]
    if msg_id not in _message_map:
        raise RuntimeError('Invalid message type received: id 0x%04X was not found in _message_map' % msg_id)
    msg = _message_map[msg_id].from_bytes(message_bytes)
    return msg


def parse_message_from_string(message_str):
    members = json.loads(message_str)
    if 'msg_id' not in members:
        raise ValueError('Failed to parse message due to missing message id')
    if members['msg_id'] not in _message_map:
        raise RuntimeError('Invalid message type received: id 0x%04X was not found in _message_map' % members['msg_id'])
    msg = _message_map[members['msg_id']].from_dict(members)
    return msg
