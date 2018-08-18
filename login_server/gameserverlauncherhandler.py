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

from ipaddress import IPv4Address
import time

from common.connectionhandler import *
from common.messages import parse_message, \
                            Login2LauncherSetPlayerLoadoutsMessage, \
                            Login2LauncherRemovePlayerLoadoutsMessage


class GameServerLauncherReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        # TODO: add validation
        return parse_message(msg_bytes)


class GameServerLauncherWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class GameServer(Peer):
    def __init__(self, ip):
        super().__init__()
        self.serverid1 = None
        self.serverid2 = None
        self.ip = ip
        self.port = None
        self.description = None
        self.motd = None
        self.playerbeingkicked = None
        self.joinable = False
        self.match_end_time = None
        self.match_time_counting = False
        self.player_ids = set()

    def set_info(self, port, description, motd):
        self.port = port
        self.description = description
        self.motd = motd
        self.joinable = True

    def set_match_time(self, seconds_remaining, counting):
        self.match_end_time = int(time.time() + seconds_remaining)
        self.match_time_counting = counting

    def get_time_remaining(self):
        if self.match_end_time is not None:
            time_remaining = int(self.match_end_time - time.time())
        else:
            time_remaining = 0

        if time_remaining < 0:
            time_remaining = 0

        return time_remaining

    def set_player_loadouts(self, player):
        msg = Login2LauncherSetPlayerLoadoutsMessage(player.unique_id, player.loadouts.loadout_dict)
        self.send(msg)
        self.player_ids.add(player.unique_id)

    def remove_player_loadouts(self, player):
        msg = Login2LauncherRemovePlayerLoadoutsMessage(player.unique_id)
        self.send(msg)
        self.player_ids.remove(player.unique_id)


class GameServerLauncherHandler(IncomingConnectionHandler):
    def __init__(self, incoming_queue):
        super().__init__('gameserverlauncher',
                         '0.0.0.0',
                         9001,
                         incoming_queue)

    def create_connection_instances(self, sock, address):
        reader = GameServerLauncherReader(sock)
        writer = GameServerLauncherWriter(sock)
        peer = GameServer(IPv4Address(address[0]))
        return reader, writer, peer


def handle_game_server_launcher(incoming_queue):
    game_controller_handler = GameServerLauncherHandler(incoming_queue)
    game_controller_handler.run()
