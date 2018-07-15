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

from datatypes import ClientMessage, \
                      ClientConnectedMessage, \
                      ClientDisconnectedMessage, \
                      constructenumblockarray, ParseError
from utils import hexdump

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

class PacketReader():
    def __init__(self, socket, dumpqueue):
        self.socket = socket
        self.buffer = bytes()
        self.dumpqueue = dumpqueue

    def recvall(self, size):
        remainingsize = size
        msg = bytes()
        while remainingsize > 0:
            chunk = self.socket.recv(remainingsize)
            if not chunk:
                raise RuntimeError('Socket connection closed')
            remainingsize -= len(chunk)
            msg += chunk
        return msg
        
    def prepare(self, length):
        ''' Makes sure that at least length bytes are available in self.buffer '''
        while len(self.buffer) < length:
            packetsizebytes = self.recvall(2)
            packetsize = struct.unpack('<H', packetsizebytes)[0]
            if packetsize == 0:
                packetsize = 1450
            packetbodybytes = self.recvall(packetsize)
            #print('Received:')
            #hexdump(packetbodybytes)
            if self.dumpqueue:
                self.dumpqueue.put(('client', packetsizebytes + packetbodybytes))
            self.buffer += packetbodybytes
            if len(packetbodybytes) != packetsize:
                raise RuntimeError('Received %d bytes, but expected %d. Client probably disconnected' %
                        (len(packetbodybytes), packetsize))

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
 
class StreamParser():
    def __init__(self, instream):
        self.instream = instream

    def parse(self):
        outfile = io.StringIO()
        nextvalue = peekshort(self.instream)

        # FIXME: That we have to look at the first short to see how 
        # many items are in this packet probably indicates that we 
        # interpret the packet structure incorrectly.
        itemcount = 1
        hasseqack = True

        if nextvalue == 0x01BC:
            hasseqack = False

        objs = []
        for i in range(itemcount):
            objs.append(constructenumblockarray(self.instream))
        if hasseqack:
            seq, _ = parseseqack(self.instream)
        else:
            seq = None

        return seq, objs


class ClientReader():
    def __init__(self, socket, clientid, clientaddress, serverqueue, dumpqueue):
        self.clientid = clientid
        self.socket = socket
        self.serverqueue = serverqueue
        self.dumpqueue = dumpqueue

        ip, port = clientaddress
        playerip = tuple(int(ippart) for ippart in ip.split('.'))

        self.serverqueue.put(ClientConnectedMessage(self.clientid, playerip, port))

    def run(self):
        packetreader = PacketReader(self.socket, self.dumpqueue)
        streamparser = StreamParser(packetreader)
        while True:
            try:
                seq, msg = streamparser.parse()
                self.serverqueue.put(ClientMessage(self.clientid, seq, msg))
                #print('client(%s): received incoming message' % self.clientid)
            except RuntimeError as e:
                print('client(%s): caught exception: %s' % (self.clientid, str(e)))
                break

        self.serverqueue.put(ClientDisconnectedMessage(self.clientid))
        print('client(%s): signalled server; reader exiting' % self.clientid)

