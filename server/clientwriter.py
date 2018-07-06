#!/usr/bin/env python3

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

