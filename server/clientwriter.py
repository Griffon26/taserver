#!/usr/bin/env python3

import gevent
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
    def __init__(self, socket, clientid, clientqueue):
        self.clientid = clientid
        self.socket = socket
        self.clientqueue = clientqueue
        self.seq = None

    def run(self):
        while True:
            stream = io.BytesIO()
            message, ack = self.clientqueue.get()
            if message is None:
                self.socket.close()
                break

            print('client(%s): processing outgoing messages (ack = %s)' % (self.clientid, ack))

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
            for packet in packetize(stream.read()):
                print('packet:')
                hexdump(packet)
                self.socket.send(packet)
        print('client(%s): writer exiting' % self.clientid)

