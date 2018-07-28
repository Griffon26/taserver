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
from configuration import Configuration
from hexdumper import HexDumper, dumpfilename
from server import Server


def handle_dump(dumpqueue):
    if dumpqueue:
        hex_dumper = HexDumper(dumpqueue)
        hex_dumper.run()


def handle_authcodes(server_queue, authcode_queue):
    authcode_handler = AuthCodeHandler(server_queue, authcode_queue)
    authcode_handler.run()


def handle_server(server_queue, client_queues, authcode_queue, accounts, configuration):
    server = Server(server_queue, client_queues, authcode_queue, accounts, configuration)
    server.run()


def handle_client(server_queue, client_queue, socket, address, dump_queue):
    myid = id(gevent.getcurrent())
    print('client(%s): connected from %s:%s' % (myid, address[0], address[1]))
    reader = ClientReader(socket, myid, address, server_queue, dump_queue)
    gevent.spawn(reader.run)

    writer = ClientWriter(socket, myid, client_queue, dump_queue)
    writer.run()


def main(dump):
    client_queues = {}
    server_queue = gevent.queue.Queue()
    authcode_queue = gevent.queue.Queue()
    dump_queue = gevent.queue.Queue() if dump else None

    accounts = Accounts('accountdatabase.json')
    configuration = Configuration()
    gevent.spawn(handle_server, server_queue, client_queues, authcode_queue, accounts, configuration)
    gevent.spawn(handle_dump, dump_queue)
    gevent.spawn(handle_authcodes, server_queue, authcode_queue)

    def handle_client_wrapper(socket, address):
        client_queue = gevent.queue.Queue()
        client_queues[id(gevent.getcurrent())] = client_queue
        handle_client(server_queue, client_queue, socket, address, dump_queue)

    server = StreamServer(('0.0.0.0', 9000), handle_client_wrapper)

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
