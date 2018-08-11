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

from .datatypes import ClientMessage, \
    ClientConnectedMessage, \
    ClientDisconnectedMessage, \
    constructenumblockarray
from common.tcpmessage import TcpMessageReader


def peekshort(infile):
    values = infile.peek(2)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('H', values)[0]


def readlong(infile):
    values = infile.read(4)
    if len(values) == 0:
        raise EOFError
    return struct.unpack('<L', values)[0]


def parseseqack(infile):
    seq = readlong(infile)
    ack = readlong(infile)
    return seq, ack


class PacketReader:
    def __init__(self, socket, dump_queue):
        self.tcp_message_reader = TcpMessageReader(socket, max_message_size = 1450)
        self.buffer = bytes()
        self.dumpqueue = dump_queue

    def prepare(self, length):
        ''' Makes sure that at least length bytes are available in self.buffer '''
        while len(self.buffer) < length:
            message_data = self.tcp_message_reader.receive()
            # print('Received:')
            # hexdump(packetbodybytes)
            if self.dumpqueue:
                packetsize = len(message_data)
                self.dumpqueue.put(('client', struct.pack('<H', packetsize) + message_data))
            self.buffer += message_data

    def read(self, length):
        self.prepare(length)
        requestedbytes = self.buffer[:length]
        self.buffer = self.buffer[length:]
        return requestedbytes

    def peek(self, length):
        self.prepare(length)
        requestedbytes = self.buffer[:length]
        return requestedbytes

    def tell(self):
        return 0


class StreamParser:
    def __init__(self, in_stream):
        self.in_stream = in_stream

    def parse(self):
        out_file = io.StringIO()
        next_value = peekshort(self.in_stream)

        # FIXME: That we have to look at the first short to see how 
        # many items are in this packet probably indicates that we 
        # interpret the packet structure incorrectly.
        item_count = 1
        has_seq_ack = True

        if next_value == 0x01BC:
            has_seq_ack = False

        objs = []
        for i in range(item_count):
            objs.append(constructenumblockarray(self.in_stream))
        if has_seq_ack:
            seq, _ = parseseqack(self.in_stream)
        else:
            seq = None

        return seq, objs


class ClientReader:
    def __init__(self, socket, client_id, client_address, server_queue, dump_queue):
        self.client_id = client_id
        self.socket = socket
        self.server_queue = server_queue
        self.dump_queue = dump_queue

        ip, port = client_address
        player_ip = tuple(int(ippart) for ippart in ip.split('.'))

        self.server_queue.put(ClientConnectedMessage(self.client_id, player_ip, port))

    def run(self):
        packet_reader = PacketReader(self.socket, self.dump_queue)
        stream_parser = StreamParser(packet_reader)
        while True:
            try:
                seq, msg = stream_parser.parse()
                self.server_queue.put(ClientMessage(self.client_id, seq, msg))
                # print('client(%s): received incoming message' % self.clientid)
            except ConnectionResetError as e:
                print('client(%s): client disconnected' % self.client_id)
                break

        self.server_queue.put(ClientDisconnectedMessage(self.client_id))
        print('client(%s): signalled server; reader exiting' % self.client_id)
