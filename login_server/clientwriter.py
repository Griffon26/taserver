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

from common.tcpmessage import TcpMessageWriter

def packetize(bytestream):
    while len(bytestream) > 0:
        chunk_size = min(len(bytestream), 1450)
        size_to_send = 0 if chunk_size == 1450 else chunk_size
        packet = struct.pack('<H', size_to_send) + bytestream[:chunk_size]
        yield packet
        bytestream = bytestream[chunk_size:]

class ClientWriter:
    def __init__(self, socket, client_id, client_queue, dump_queue):
        self.client_id = client_id
        self.socket = socket
        self.tcp_writer = TcpMessageWriter(socket, max_message_size = 1450)
        self.client_queue = client_queue
        self.dump_queue = dump_queue
        self.seq = None

    def run(self):
        while True:
            stream = io.BytesIO()
            message, ack = self.client_queue.get()
            if message is None:
                print('client(%s): writer closing socket' % self.client_id)
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

            # Instead of just using the tcp_writer we have to first collect the bytes of all
            # messages and then send them in one call, otherwise Tribes Ascend cannot deal
            # with it.
            '''
            while True:
                chunk = stream.read(1450)
                if not chunk:
                    break
                self.tcp_writer.send(chunk)
            '''
            packet_stream = io.BytesIO()
            for packet in packetize(stream.read()):
                if self.dump_queue:
                    self.dump_queue.put(('server', packet))

                packet_stream.write(packet)

            packet_stream.seek(0)
            self.socket.sendall(packet_stream.read())


        print('client(%s): writer exiting gracefully' % self.client_id)

