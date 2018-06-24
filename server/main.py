#!/usr/bin/env python3

import gevent
import gevent.queue
from gevent.server import StreamServer
from clientreader import ClientReader
from clientwriter import ClientWriter
from server import Server

def handleserver(serverqueue, clientqueues):
    server = Server(serverqueue, clientqueues)
    server.run()

def handleclient(serverqueue, clientqueue, socket, address):
    myid = id(gevent.getcurrent())
    print('client(%s): connected' % myid)
    reader = ClientReader(socket, myid, serverqueue)
    gevent.spawn(reader.run)

    writer = ClientWriter(socket, myid, clientqueue)
    writer.run()

def main():
    serverqueue = gevent.queue.Queue()
    clientqueues = {}
    gevent.spawn(handleserver, serverqueue, clientqueues)

    def handleclientwrapper(socket, address):
        clientqueue = gevent.queue.Queue()
        clientqueues[id(gevent.getcurrent())] = clientqueue
        handleclient(serverqueue, clientqueue, socket, address)

    server = StreamServer(('0.0.0.0', 9000), handleclientwrapper)
    server.serve_forever()

if __name__ == '__main__':
    main()

