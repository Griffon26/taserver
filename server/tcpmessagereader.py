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

class TcpMessageReader:
    def __init__(self, socket):
        self.socket = socket

    def _recvall(self, size):
        remaining_size = size
        msg = bytes()
        while remaining_size > 0:
            chunk = self.socket.recv(remaining_size)
            if not chunk:
                raise RuntimeError('Socket connection closed')
            remaining_size -= len(chunk)
            msg += chunk
        return msg

    def receive(self):
        packetsizebytes = self._recvall(2)
        packetsize = struct.unpack('<H', packetsizebytes)[0]
        if packetsize == 0:
            packetsize = 1450
        packetbodybytes = self._recvall(packetsize)
        if len(packetbodybytes) != packetsize:
            raise RuntimeError('Received %d bytes, but expected %d. What happened?' %
                               (len(packetbodybytes), packetsize))
        return packetbodybytes
