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

import gevent.monkey
gevent.monkey.patch_socket()

import gevent
import socket


class LoginServerReader():
    def __init__(self, sock, incoming_queue):
        self.sock = sock
        self.incoming_queue = incoming_queue

    def run(self):
        while True:
            print('LoginServerReader tick')
            gevent.sleep(5)


class LoginServerWriter():
    def __init__(self, sock, outgoing_queue):
        self.sock = sock
        self.outgoing_queue = outgoing_queue

    def run(self):
        while True:
            print('LoginServerWriter tick')
            gevent.sleep(5)

def handle_login_server(login_server_config, incoming_queue, outgoing_queue):
    gevent.getcurrent().name = 'login_server_handler'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((login_server_config['host'], login_server_config['port']))

    reader = LoginServerReader(sock, incoming_queue)
    gevent.spawn(reader.run)

    writer = LoginServerWriter(sock, outgoing_queue)
    writer.run()