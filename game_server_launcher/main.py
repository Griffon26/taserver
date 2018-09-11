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

import configparser
import gevent
import gevent.queue
import logging
import os

from common.logging import set_up_logging
from .gamecontrollerhandler import handle_game_controller
from .gameserverhandler import run_game_server, ConfigurationError
from .launcher import handle_launcher, IncompatibleVersionError
from .loginserverhandler import handle_login_server
from .pinghandler import handle_ping

INI_PATH = os.path.join('data', 'gameserverlauncher.ini')


def main():
    set_up_logging('game_server_launcher.log')
    logger = logging.getLogger(__name__)
    config = configparser.ConfigParser()
    with open(INI_PATH) as f:
        config.read_file(f)

    restart = True
    restart_delay = 10
    tasks = []
    try:
        while restart:
            incoming_queue = gevent.queue.Queue()

            tasks = [
                gevent.spawn(handle_ping),
                gevent.spawn(run_game_server, config['gameserver']),
                gevent.spawn(handle_login_server, config['loginserver'], incoming_queue),
                gevent.spawn(handle_game_controller, config['gamecontroller'], incoming_queue),
                gevent.spawn(handle_launcher, config['gameserver'], incoming_queue)
            ]

            # Wait for any of the tasks to terminate
            finished_greenlets = gevent.joinall(tasks, count=1)

            logger.warning('The following greenlets terminated: %s' % ','.join([g.name for g in finished_greenlets]))

            configuration_errors = ['  %s' % g.exception for g in finished_greenlets
                                    if isinstance(g.exception, ConfigurationError)]
            if configuration_errors:
                logger.critical('\n' +
                    '\n-------------------------------------------\n' +
                    'Found errors in configuration files:' +
                    '\n'.join(configuration_errors) +
                    '\n-------------------------------------------\n'
                )
                restart = False

            incompatible_version_errors = ['  %s' % g.exception for g in finished_greenlets
                                           if isinstance(g.exception, IncompatibleVersionError)]
            if incompatible_version_errors:
                logger.critical('\n' +
                    '\n-------------------------------------------\n' +
                    'A version incompatibility was found:' +
                    '\n'.join(incompatible_version_errors) +
                    '\n-------------------------------------------\n'
                )
                restart = False

            logger.info('Killing all tasks...')
            gevent.killall(tasks)
            logger.info('Waiting %s seconds before %s...' %
                        (restart_delay, ('restarting' if restart else 'exiting')))
            gevent.sleep(restart_delay)

    except KeyboardInterrupt:
        gevent.killall(tasks)
