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

import argparse
import gevent
import gevent.queue
from gevent.server import StreamServer

from accounts import Accounts
from authcodehandler import AuthCodeHandler
from clientreader import ClientReader
from clientwriter import ClientWriter
from hexdumper import HexDumper, dumpfilename
from server import Server


def handledump(dumpqueue):
    if dumpqueue:
        hexdumper = HexDumper(dumpqueue)
        hexdumper.run()

def handleauthcodes(serverqueue, authcodequeue):
    authcodehandler = AuthCodeHandler(serverqueue, authcodequeue)
    authcodehandler.run()

def handleserver(serverqueue, clientqueues, authcodequeue, accounts):
    server = Server(serverqueue, clientqueues, authcodequeue, accounts)
    server.run()

def handleclient(serverqueue, clientqueue, socket, address, dumpqueue):
    myid = id(gevent.getcurrent())
    print('client(%s): connected from %s:%s' % (myid, address[0], address[1]))
    reader = ClientReader(socket, myid, address, serverqueue, dumpqueue)
    gevent.spawn(reader.run)

    writer = ClientWriter(socket, myid, clientqueue, dumpqueue)
    writer.run()

def main(dump):
    clientqueues = {}
    serverqueue = gevent.queue.Queue()
    authcodequeue = gevent.queue.Queue()
    dumpqueue = gevent.queue.Queue() if dump else None

    accounts = Accounts('accountdatabase.json')
    
    gevent.spawn(handleserver, serverqueue, clientqueues, authcodequeue, accounts)
    gevent.spawn(handledump, dumpqueue)
    gevent.spawn(handleauthcodes, serverqueue, authcodequeue)

    def handleclientwrapper(socket, address):
        clientqueue = gevent.queue.Queue()
        clientqueues[id(gevent.getcurrent())] = clientqueue
        handleclient(serverqueue, clientqueue, socket, address, dumpqueue)

    server = StreamServer(('0.0.0.0', 9000), handleclientwrapper)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        accounts.save()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true',
                        help='Dump all traffic to %s in a format suitable '
                             'for parsing with the parse.py utility.' %
                             dumpfilename)
    args = parser.parse_args()
    main(args.dump)

