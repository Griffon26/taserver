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

from gevent import socket
import struct

from .datatypes import AuthCodeRequestMessage

authcode_address = ('127.0.0.1', 9800)


class AuthCodeHandler:
    def __init__(self, server_queue, authcode_queue):
        self.server_queue = server_queue
        self.authcode_queue = authcode_queue

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(authcode_address)
        while True:
            data, addr = sock.recvfrom(4096)
            length = struct.unpack('<H', data[0:2])[0]
            name_from_client = data[2:2 + length].decode('latin1')
            self.server_queue.put(AuthCodeRequestMessage(name_from_client))

            name_from_server, authcode = self.authcode_queue.get()
            if name_from_server != name_from_client:
                raise RuntimeError('bug!')
            sock.sendto(struct.pack('<H', len(authcode)) + authcode.encode('latin1'), addr)
