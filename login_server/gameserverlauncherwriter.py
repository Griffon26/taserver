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

import struct

from common.tcpmessage import TcpMessageWriter


def packetize(bytestream):
    while len(bytestream) > 0:
        chunk_size = min(len(bytestream), 1450)
        size_to_send = 0 if chunk_size == 1450 else chunk_size
        packet = struct.pack('<H', size_to_send) + bytestream[:chunk_size]
        yield packet
        bytestream = bytestream[chunk_size:]


class GameServerLauncherWriter:
    def __init__(self, socket, game_server_id, game_server_queue):
        self.game_server_id = game_server_id
        self.message_writer = TcpMessageWriter(socket)
        self.game_server_queue = game_server_queue

    def run(self):
        while True:
            message = self.game_server_queue.get()
            if message is None:
                print('gameserverlauncher(%s): writer closing socket' % self.game_server_id)
                self.message_writer.close()
                break

            self.message_writer.send(message)

        print('gameserverlauncher(%s): writer exiting gracefully' % self.game_server_id)

