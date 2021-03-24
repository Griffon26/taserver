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

from gevent import monkey
monkey.patch_all()

import argparse
import configparser
import gevent
import gevent.queue
import logging
import os
import sys

from common.geventwrapper import gevent_spawn
from common.logging import set_up_logging
from common.migration_mechanism import run_migrations
from common.ports import Ports
from common.utils import get_shared_ini_path
from .accounts import Accounts
from .authcodehandler import handle_authcodes
from .gameserverlauncherhandler import handle_game_server_launcher
from .gameclienthandler import handle_game_client
from .httphandler import handle_http
from .trafficdumper import TrafficDumper, dumpfilename
from .loginserver import LoginServer
from .webhookhandler import handle_webhook


def handle_dump(dumpqueue):
    gevent.getcurrent().name = 'trafficdumper'
    if dumpqueue:
        traffic_dumper = TrafficDumper(dumpqueue)
        traffic_dumper.run()


def handle_server(server_queue, client_queues, server_stats_queue, ports, accounts):
    server = LoginServer(server_queue, client_queues, server_stats_queue, ports, accounts)
    # server.trace_as('loginserver')
    server.run()


def main():
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dump', action='store_true',
                        help='Dump all traffic to %s in a format suitable '
                             'for parsing with the parse.py utility.' %
                             dumpfilename)
    parser.add_argument('--data-root', action='store', default='data',
                        help='Location of the data dir containing all config files and logs.')
    args = parser.parse_args()
    data_root = args.data_root
    
    set_up_logging(data_root, 'login_server.log')

    # Perform data migrations on startup
    try:
        run_migrations(data_root)
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
    server_stats_queue = gevent.queue.Queue()
    dump_queue = gevent.queue.Queue() if args.dump else None

    accounts = Accounts(os.path.join(data_root, 'accountdatabase.json'))
    config = configparser.ConfigParser()
    with open(os.path.join(data_root, 'loginserver.ini')) as f:
        config.read_file(f)
    with open(get_shared_ini_path(data_root)) as f:
        config.read_file(f)

    ports = Ports(int(config['shared']['port_offset']))

    tasks = [
        gevent_spawn("login server's handle_server",
                     handle_server,
                     server_queue,
                     client_queues,
                     server_stats_queue,
                     ports,
                     accounts),
        gevent_spawn("login server's handle_authcodes",
                     handle_authcodes,
                     server_queue),
        gevent_spawn("login server's handle_webhook",
                     handle_webhook,
                     server_stats_queue,
                     config['loginserver']),
        gevent_spawn("login server's handle_http",
                     handle_http,
                     server_queue,
                     ports),
        gevent_spawn("login server's handle_game_client",
                     handle_game_client,
                     server_queue, dump_queue, data_root),
        gevent_spawn("login server's handle_game_server_launcher",
                     handle_game_server_launcher,
                     server_queue,
                     ports)
    ]
    # Give the greenlets enough time to start up, otherwise killall can block
    gevent.sleep(1)

    if dump_queue:
        tasks.append(gevent_spawn("login server's handle_dump", handle_dump, dump_queue))

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
