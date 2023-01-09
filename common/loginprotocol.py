#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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
from common.token_bucket import TokenBucket

from .datatypes import construct_top_level_enumfield, m034a


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
        next_object = construct_top_level_enumfield(self.in_stream)

        # FIXME: That we have to look at the first object to see how
        # many items are in this packet probably indicates that we
        # interpret the packet structure incorrectly.
        if next_object.ident == 0x003d and next_object.findbytype(m034a):
            additional_item_count = 11
        else:
            additional_item_count = 0
        has_seq_ack = True

        if next_object.ident == 0x01bc:
            has_seq_ack = False

        objs = [next_object]
        for i in range(additional_item_count):
            objs.append(construct_top_level_enumfield(self.in_stream))
        if has_seq_ack:
            seq, _ = parseseqack(self.in_stream)
        else:
            seq = None

        return seq, objs


class LoginProtocolMessage():
    def __init__(self, clientseq, requests):
        self.clientseq = clientseq
        self.requests = requests


class LoginProtocolReader(TcpMessageConnectionReader):
    def __init__(self, sock, dump_queue, token_bucket_data: TokenBucket = None, token_bucket_msgs: TokenBucket = None):
        super().__init__(sock, max_message_size=1450, dump_queue=dump_queue, token_bucket=token_bucket_data)
        packet_reader = PacketReader(super().receive)
        self.stream_parser = StreamParser(packet_reader)
        self.token_bucket_msgs = token_bucket_msgs

    def receive(self):
        return None

    def decode(self, msg_bytes):
        seq, msg = self.stream_parser.parse()
        if self.token_bucket_msgs and not self.token_bucket_msgs.consume(1):
            raise RateLimitError(f'exceeded token bucket limit of {str(self.token_bucket_msgs)}')
        return LoginProtocolMessage(seq, msg)


class LoginProtocolWriter(TcpMessageConnectionWriter):
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
