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

from common.messages import parse_message_from_bytes
from common.connectionhandler import *


class GameControllerReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        return parse_message_from_bytes(msg_bytes)


class GameControllerWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class GameController(Peer):
    pass


class GameControllerHandler(IncomingConnectionHandler):
    def __init__(self, ports, incoming_queue):
        super().__init__('gamecontroller',
                         '127.0.0.1',
                         ports['game2launcher'],
                         incoming_queue)

    def create_connection_instances(self, sock, address):
        reader = GameControllerReader(sock)
        writer = GameControllerWriter(sock)
        peer = GameController()
        return reader, writer, peer


def handle_game_controller(game_controller_config, incoming_queue):
    game_controller_handler = GameControllerHandler(game_controller_config, incoming_queue)
    game_controller_handler.run()
