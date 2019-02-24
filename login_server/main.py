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
import sys
import gevent
import gevent.queue
import logging

from common.logging import set_up_logging
from common.migration_mechanism import run_migrations
from .accounts import Accounts
from .authcodehandler import handle_authcodes
from .configuration import Configuration
from .gameserverlauncherhandler import handle_game_server_launcher
from .gameclienthandler import handle_game_client
from .trafficdumper import TrafficDumper, dumpfilename
from .loginserver import LoginServer


def handle_dump(dumpqueue):
    gevent.getcurrent().name = 'trafficdumper'
    if dumpqueue:
        traffic_dumper = TrafficDumper(dumpqueue)
        traffic_dumper.run()


def handle_server(server_queue, client_queues, accounts, configuration):
    server = LoginServer(server_queue, client_queues, accounts, configuration)
    # server.trace_as('loginserver')
    server.run()


def main():
    set_up_logging('login_server.log')
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true',
                        help='Dump all traffic to %s in a format suitable '
                             'for parsing with the parse.py utility.' %
                             dumpfilename)
    args = parser.parse_args()

    # Perform data migrations on startup
    try:
        run_migrations('data')
    except ValueError as e:
        # If a migration failed, it will raise a ValueError
        logger.fatal('Failed to run data migrations with format error: %s' % str(e))
        sys.exit(2)
    except OSError as e:
        # If a migration failed, it will raise a ValueError
        logger.fatal('Failed to run data migrations with OS error: %s' % str(e))
        sys.exit(2)
    
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
    # Give the greenlets enough time to start up, otherwise killall can block
    gevent.sleep(1)

    if dump_queue:
        tasks.append(gevent.spawn(handle_dump, dump_queue))

    try:
        # Wait for any of the tasks to terminate
        finished_greenlets = gevent.joinall(tasks, count=1)

        logger.error('The following greenlets terminated: %s' % ','.join([g.name for g in finished_greenlets]))

        exceptions = ['  %s' % g.exception for g in finished_greenlets
                                if isinstance(g.exception, Exception)]
        if exceptions:
            logger.critical('\n' +
                            '\n-------------------------------------------\n' +
                            'The following exceptions occurred:\n' +
                            '\n'.join(exceptions) +
                            '\n-------------------------------------------\n'
                            )

        if dump_queue:
            logger.info('Giving the dump greenlet some time to finish writing to disk...')
            gevent.sleep(2)

        logger.info('Killing everything and waiting 10 seconds before exiting...')
        gevent.killall(tasks)
        gevent.sleep(5)

    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received. Exiting...')
        gevent.killall(tasks)
        accounts.save()
    except Exception:
        logger.exception('Main login server thread exited with an exception')
