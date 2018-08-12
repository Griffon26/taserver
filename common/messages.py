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

# These IDs should only be extended, not changed, to allow for some
# backward compatibility

_MSGID_LOGIN2LAUNCHER_NEXTMAP = 0x1000
_MSGID_LOGIN2LAUNCHER_SETPLAYERLOADOUTS = 0x1001

_MSGID_LAUNCHER2LOGIN_SERVERINFO = 0x2000
_MSGID_LAUNCHER2LOGIN_MAPINFO = 0x2001
_MSGID_LAUNCHER2LOGIN_TEAMINFO = 0x2002
_MSGID_LAUNCHER2LOGIN_MATCHEND = 0x2003
_MSGID_LAUNCHER2LOGIN_SCOREINFO = 0x2004
_MSGID_LAUNCHER2LOGIN_MATCHTIME = 0x2005

_MSGID_GAME2LAUNCHER_TEAMSWITCH = 0x3000
_MSGID_GAME2LAUNCHER_MATCHTIME = 0x3001
_MSGID_GAME2LAUNCHER_LOADOUTREQUEST = 0x3002

_MSGID_LAUNCHER2GAME_LOADOUT = 0x4000


class Message:
    def to_bytes(self):
        return struct.pack('<H', self.msg_id) + bytes(json.dumps(self.__dict__), encoding='utf8')

    @classmethod
    def from_bytes(cls, data):
        msg_id = struct.unpack('<H', data[0:2])[0]
        if msg_id != cls.msg_id:
            raise ValueError('Cannot parse object of this type from these bytes')

        members = json.loads(data[2:])
        return cls(**members)


class Login2LauncherNextMapMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_NEXTMAP


class Login2LauncherSetPlayerLoadoutsMessage(Message):
    msg_id = _MSGID_LOGIN2LAUNCHER_SETPLAYERLOADOUTS

    def __init__(self, unique_id, loadouts):
        self.unique_id = unique_id
        self.loadouts = loadouts


class Launcher2LoginServerInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_SERVERINFO

    def __init__(self, port, description, motd):
        self.port = port
        self.description = description
        self.motd = motd


class Launcher2LoginMapInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MAPINFO


class Launcher2LoginTeamInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_TEAMINFO


class Launcher2LoginMatchEndMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MATCHEND


class Launcher2LoginScoreInfoMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_SCOREINFO


class Launcher2LoginMatchTimeMessage(Message):
    msg_id = _MSGID_LAUNCHER2LOGIN_MATCHTIME


class Game2LauncherTeamSwitchMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_TEAMSWITCH


class Game2LauncherMatchTimeMessage(Message):
    msg_id = _MSGID_GAME2LAUNCHER_MATCHTIME


class Game2LauncherLoadoutRequest(Message):
    msg_id = _MSGID_GAME2LAUNCHER_LOADOUTREQUEST

    def __init__(self, player_unique_id, class_id, loadout_number):
        self.player_unique_id = player_unique_id
        self.class_id = class_id
        self.loadout_number = loadout_number


class Launcher2GameLoadoutMessage(Message):
    msg_id = _MSGID_LAUNCHER2GAME_LOADOUT

    def __init__(self, loadout):
        self.loadout = loadout


_message_classes = [
    Login2LauncherNextMapMessage,
    Login2LauncherSetPlayerLoadoutsMessage,

    Launcher2LoginServerInfoMessage,
    Launcher2LoginMapInfoMessage,
    Launcher2LoginTeamInfoMessage,
    Launcher2LoginMatchEndMessage,
    Launcher2LoginScoreInfoMessage,
    Launcher2LoginMatchTimeMessage,

    Game2LauncherTeamSwitchMessage,
    Game2LauncherMatchTimeMessage,

    Launcher2GameLoadoutMessage,
]

_message_map = { msg_class.msg_id : msg_class for msg_class in _message_classes }

def parse_message(message_bytes):
    msg_id = struct.unpack('<H', message_bytes[0:2])[0]
    msg = _message_map[msg_id].from_bytes(message_bytes)
    return msg
