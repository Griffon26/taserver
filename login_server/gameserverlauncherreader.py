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

from .datatypes import GameServerConnectedMessage, GameServerDisconnectedMessage
from common.tcpmessage import TcpMessageReader
from common.messages import parse_message


class GameServerLauncherReader:
    def __init__(self, socket, game_server_id, game_server_address, server_queue):
        self.game_server_id = game_server_id
        self.tcp_reader = TcpMessageReader(socket)
        self.server_queue = server_queue

        ip, port = game_server_address
        server_ip = IPv4Address(ip)

        self.server_queue.put(GameServerConnectedMessage(self.game_server_id, server_ip, port))

    def run(self):
        try:
            while True:
                msg_bytes = self.tcp_reader.receive()
                msg = parse_message(msg_bytes)
                msg.game_server_id = self.game_server_id
                self.server_queue.put(msg)

        except ConnectionResetError as e:
            print('gameserverlauncher(%s): disconnected' % self.game_server_id)

        self.server_queue.put(GameServerDisconnectedMessage(self.game_server_id))
        print('gameserverlauncher(%s): signalled server; reader exiting' % self.game_server_id)
