#!/usr/bin/env python3

import argparse
import gevent
import gevent.queue
from gevent.server import StreamServer
from clientreader import ClientReader
from clientwriter import ClientWriter
from server import Server

dumpfilename = 'taserverdump.hexdump'

def handledump(dumpqueue):
    if not dumpqueue:
        return

    clientoffset = 0
    serveroffset = 0
    with open(dumpfilename, 'wt') as dumpfile:
        while True:
            source, packetbytes = dumpqueue.get()
            indent = '    ' if source == 'server' else ''
            bytelist = [ '%02X' % b for b in packetbytes ]
            offset = 0
            while len(bytelist) > offset + 16:
                dumpfile.write('%s%04X  %s   .\n' % (indent, clientoffset + offset, ' '.join(bytelist[offset:offset + 16])))
                offset += 16
            dumpfile.write('%s%04X  %s   .\n' % (indent, offset, ' '.join(bytelist[offset:])))
            dumpfile.flush()

def handleserver(serverqueue, clientqueues):
    server = Server(serverqueue, clientqueues)
    server.run()

def handleclient(serverqueue, clientqueue, socket, address, dumpqueue):
    myid = id(gevent.getcurrent())
    print('client(%s): connected' % myid)
    reader = ClientReader(socket, myid, serverqueue, dumpqueue)
    gevent.spawn(reader.run)

    writer = ClientWriter(socket, myid, clientqueue, dumpqueue)
    writer.run()

def main(dump):
    clientqueues = {}
    serverqueue = gevent.queue.Queue()
    dumpqueue = gevent.queue.Queue() if dump else None
    
    gevent.spawn(handleserver, serverqueue, clientqueues)
    gevent.spawn(handledump, dumpqueue)

    def handleclientwrapper(socket, address):
        clientqueue = gevent.queue.Queue()
        clientqueues[id(gevent.getcurrent())] = clientqueue
        handleclient(serverqueue, clientqueue, socket, address, dumpqueue)

    server = StreamServer(('0.0.0.0', 9000), handleclientwrapper)
    server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true',
                        help='Dump all traffic to %s in a format suitable '
                             'for parsing with the parse.py utility.' %
                             dumpfilename)
    args = parser.parse_args()
    main(args.dump)

