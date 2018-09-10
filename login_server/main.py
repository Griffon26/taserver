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

from .accounts import Accounts
from .authcodehandler import handle_authcodes
from .configuration import Configuration
from .gameserverlauncherhandler import handle_game_server_launcher
from .gameclienthandler import handle_game_client
from .hexdumper import HexDumper, dumpfilename
from .loginserver import LoginServer


def handle_dump(dumpqueue):
    gevent.getcurrent().name = 'hexdumper'
    if dumpqueue:
        hex_dumper = HexDumper(dumpqueue)
        hex_dumper.run()


def handle_server(server_queue, client_queues, accounts, configuration):
    server = LoginServer(server_queue, client_queues, accounts, configuration)
    server.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true',
                        help='Dump all traffic to %s in a format suitable '
                             'for parsing with the parse.py utility.' %
                             dumpfilename)
    args = parser.parse_args()
    
    client_queues = {}
    server_queue = gevent.queue.Queue()
    dump_queue = gevent.queue.Queue() if args.dump else None

    accounts = Accounts('data/accountdatabase.json')
    configuration = Configuration()

    tasks = [
        gevent.spawn(handle_server, server_queue, client_queues, accounts, configuration),
        gevent.spawn(handle_authcodes, server_queue),
        gevent.spawn(handle_game_client, server_queue, dump_queue),
        gevent.spawn(handle_game_server_launcher, server_queue)
    ]

    if dump_queue:
        tasks.append(gevent.spawn(handle_dump, dump_queue))

    try:
        # Wait for any of the tasks to terminate
        finished_greenlets = gevent.joinall(tasks, count=1)

        print('The following greenlets terminated: %s' % ','.join([g.name for g in finished_greenlets]))

        if dump_queue:
            print('Giving the dump greenlet some time to finish writing to disk...')
            gevent.sleep(2)

        print('Killing everything and waiting 10 seconds before exiting...')
        gevent.killall(tasks)
        gevent.sleep(5)

    except KeyboardInterrupt:
        gevent.killall(tasks)
        accounts.save()
