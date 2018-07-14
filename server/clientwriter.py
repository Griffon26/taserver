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

import io
import struct

from utils import hexdump

def packetize(bytestream):
    while len(bytestream) > 0:
        chunksize = min(len(bytestream), 1450)
        sizetosend = 0 if chunksize == 1450 else chunksize
        packet = struct.pack('<H', sizetosend) + bytestream[:chunksize]
        yield packet
        bytestream = bytestream[chunksize:]

class ClientWriter():
    def __init__(self, socket, clientid, clientqueue, dumpqueue):
        self.clientid = clientid
        self.socket = socket
        self.clientqueue = clientqueue
        self.dumpqueue = dumpqueue
        self.seq = None

    def run(self):
        while True:
            stream = io.BytesIO()
            message, ack = self.clientqueue.get()
            if message is None:
                print('client(%s): writer closing socket' % self.clientid)
                self.socket.close()
                break

            #print('client(%s): processing outgoing messages (ack = %s)' % (self.clientid, ack))

            if isinstance(message, list):
                for el in message:
                    el.write(stream)
            else:
                message.write(stream)

            if ack is None:
                ack = 0
            if self.seq is not None:
                stream.write(struct.pack('<LL', self.seq, ack))
                self.seq += 1
            else:
                self.seq = 0

            stream.seek(0)
            packetstream = io.BytesIO()
            for packet in packetize(stream.read()):
                if self.dumpqueue:
                    self.dumpqueue.put(('server', packet))

                packetstream.write(packet)

            packetstream.seek(0)
            self.socket.sendall(packetstream.read())
                
                    
        print('client(%s): writer exiting gracefully' % self.clientid)

