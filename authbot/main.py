#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import gevent.monkey
gevent.monkey.patch_all()

import argparse
import configparser
import gevent
import gevent.queue
import logging
import os

from common.ports import Ports
from common.errors import FatalError, MajorError
from common.geventwrapper import gevent_spawn
from common.logging import set_up_logging
from .authbot import handle_authbot
from .communityloginserverhandler import handle_community_login_server
from .hirezloginserverhandler import handle_hirez_login_server

INI_FILE = 'authbot.ini'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', action='store', default='data',
                        help='Location of the data dir containing all config files and logs.')
    args = parser.parse_args()
    data_root = args.data_root
    set_up_logging(data_root, 'authbot.log')
    logger = logging.getLogger(__name__)
    config = configparser.ConfigParser()
    with open(os.path.join(data_root, INI_FILE)) as f:
        config.read_file(f)

    # We're only gonna use fixed ports, so no need to read port offset from the config
    ports = Ports(0)

    restart = True
    tasks = []
    try:
        while restart:
            incoming_queue = gevent.queue.Queue()

            tasks = [
                gevent_spawn("authbot's handle_authbot",
                             handle_authbot,
                             config['authbot'],
                             incoming_queue),
                gevent_spawn("authbot's handle_hirez_login_server",
                             handle_hirez_login_server,
                             config['authbot'],
                             ports,
                             incoming_queue),
                gevent_spawn("authbot's handle_community_login_server",
                             handle_community_login_server,
                             ports,
                             incoming_queue),
            ]

            # Wait for any of the tasks to terminate
            finished_greenlets = gevent.joinall(tasks, count=1)

            logger.warning('The following greenlets terminated: %s' % ','.join([g.name for g in finished_greenlets]))

            restart_delay = 10

            fatal_errors = ['  %s' % g.exception for g in finished_greenlets
                            if isinstance(g.exception, FatalError)]
            if fatal_errors:
                logger.critical('\n' +
                    '\n-------------------------------------------\n' +
                    'The following fatal errors occurred:\n' +
                    '\n'.join(fatal_errors) +
                    '\n-------------------------------------------\n'
                )
                restart = False

            major_errors = ['  %s' % g.exception for g in finished_greenlets
                            if isinstance(g.exception, MajorError)]
            if major_errors:
                logger.critical('\n' +
                    '\n-------------------------------------------\n' +
                    'The following major errors occurred:\n' +
                    '\n'.join(major_errors) +
                    '\n-------------------------------------------\n'
                )
                restart_delay = 15 * 60

            logger.info('Killing all tasks...')
            gevent.killall(tasks)
            logger.info('Waiting %s seconds before %s...' %
                        (restart_delay, ('restarting' if restart else 'exiting')))
            gevent.sleep(restart_delay)

    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received. Exiting...')
        gevent.killall(tasks)
    except Exception:
        logger.exception('Main authbot thread exited with an exception')
