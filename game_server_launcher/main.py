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
from gevent.server import StreamServer
import os

from .gameserverhandler import run_game_server
from .loginserverhandler import handle_login_server
from .gamecontrollerhandler import handle_game_controller
from .launcherhandler import handle_launcher
from common import messages

INI_PATH = os.path.join('data', 'gameserverlauncher.ini')


def main():
    game_controller_queue = gevent.queue.Queue()
    login_server_queue = gevent.queue.Queue()
    incoming_queue = gevent.queue.Queue()

    config = configparser.ConfigParser()
    with open(INI_PATH) as f:
        config.read_file(f)

    try:
        while True:
            tasks = [
                gevent.spawn(run_game_server, config['gameserver']),
                gevent.spawn(handle_login_server, config['loginserver'], incoming_queue, login_server_queue),
                gevent.spawn(handle_game_controller, config['gamecontrollerhandler'], incoming_queue, game_controller_queue),
                gevent.spawn(handle_launcher, config['gameserver'], incoming_queue, login_server_queue, game_controller_queue)
            ]

            # Wait for any of the tasks to terminate
            finished_greenlets = gevent.joinall(tasks, count = 1)

            print('The following greenlets terminated: %s' % ','.join([g.name for g in finished_greenlets]))
            print('Killing everything and waiting 5 seconds before restarting...')
            gevent.killall(tasks)
            gevent.sleep(5)

    except KeyboardInterrupt:
        gevent.killall(tasks)
