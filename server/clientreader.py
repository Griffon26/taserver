#!/usr/bin/env python3

import gevent
import io
import struct

from datatypes import constructenumblockarray, ParseError
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
    def __init__(self, socket):
        self.socket = socket
        self.buffer = bytes()

    def prepare(self, length):
        ''' Makes sure that at least length bytes are available in self.buffer '''
        while len(self.buffer) < length:
            packetsizebytes = self.socket.recv(2)
            if len(packetsizebytes) == 0:
                raise RuntimeError('client disconnected')
            packetsize = struct.unpack('<H', packetsizebytes)[0]
            if packetsize == 0:
                packetsize = 1450
            packetbodybytes = self.socket.recv(packetsize)
            print('Received:')
            hexdump(packetbodybytes)
            self.buffer += packetbodybytes
            if len(packetbodybytes) != packetsize:
                raise ParseError('The number of bytes available in the file (%d) is not equal to the number of bytes expected (%d)' %
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
    def __init__(self, socket, clientid, serverqueue):
        self.clientid = clientid
        self.socket = socket
        self.serverqueue = serverqueue

    def run(self):
        packetreader = PacketReader(self.socket)
        streamparser = StreamParser(packetreader)
        while True:
            try:
                seq, msg = streamparser.parse()
                self.serverqueue.put((self.clientid, seq, msg))
                print('client(%s): received incoming message' % self.clientid)
            except RuntimeError as e:
                print('client(%s): caught %s' % (self.clientid, str(e)))
                break

        self.serverqueue.put((self.clientid, None, None))
        print('client(%s): reader exiting' % self.clientid)

