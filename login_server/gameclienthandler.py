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

from common.connectionhandler import *
from .datatypes import ClientMessage, constructenumblockarray
from .player.player import Player


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
    def __init__(self, receive_func):
        self.buffer = bytes()
        self.receive_func = receive_func

    def prepare(self, length):
        ''' Makes sure that at least length bytes are available in self.buffer '''
        while len(self.buffer) < length:
            message_data = self.receive_func()
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


class GameClientReader(TcpMessageConnectionReader):
    def __init__(self, sock, dump_queue):
        super().__init__(sock, max_message_size = 1450, dump_queue = dump_queue)
        packet_reader = PacketReader(super().receive)
        self.stream_parser = StreamParser(packet_reader)

    def receive(self):
        return None

    def decode(self, msg_bytes):
        seq, msg = self.stream_parser.parse()
        return ClientMessage(seq, msg)


class GameClientWriter(TcpMessageConnectionWriter):
    def __init__(self, sock, dump_queue):
        super().__init__(sock, max_message_size = 1450, dump_queue = dump_queue)
        self.seq = None

    def encode(self, msg_tuple):
        stream = io.BytesIO()
        message, ack = msg_tuple

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

        return stream.getvalue()


class GameClientHandler(IncomingConnectionHandler):
    def __init__(self, incoming_queue, dump_queue):
        super().__init__('gameclient',
                         '0.0.0.0',
                         9000,
                         incoming_queue)
        self.dump_queue = dump_queue

    def create_connection_instances(self, sock, address):
        reader = GameClientReader(sock, self.dump_queue)
        writer = GameClientWriter(sock, self.dump_queue)
        peer = Player(address)
        return reader, writer, peer


def handle_game_client(incoming_queue, dump_queue):
    game_client_handler = GameClientHandler(incoming_queue, dump_queue)
    game_client_handler.run()
