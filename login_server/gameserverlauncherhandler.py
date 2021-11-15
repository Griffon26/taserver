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

from common.connectionhandler import *
from common.messages import parse_message_from_bytes
from .gameserver import GameServer


class GameServerLauncherReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        # TODO: add validation
        return parse_message_from_bytes(msg_bytes)


class GameServerLauncherWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class GameServerLauncherHandler(IncomingConnectionHandler):
    def __init__(self, incoming_queue, ports, shared_config):
        super().__init__('gameserverlauncher',
                         '0.0.0.0',
                         ports['launcher2login'],
                         incoming_queue)
        self.ports = ports
        self.shared_config = shared_config

    def create_connection_instances(self, sock, address):
        reader = GameServerLauncherReader(sock)
        writer = GameServerLauncherWriter(sock)
        peer = GameServer(IPv4Address(address[0]), self.ports, self.shared_config)
        return reader, writer, peer


def handle_game_server_launcher(incoming_queue, ports, shared_config):
    game_controller_handler = GameServerLauncherHandler(incoming_queue, ports, shared_config)
    game_controller_handler.run()
