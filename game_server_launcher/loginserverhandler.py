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
from ipaddress import IPv4Address
import socket

from common.tcpmessage import TcpMessageReader, TcpMessageWriter
from common.messages import parse_message
from .launchermessages import LoginServerDisconnectedMessage

class LoginServerReader():
    def __init__(self, my_id, sock, incoming_queue):
        self.my_id = my_id
        self.tcp_reader = TcpMessageReader(sock)
        self.incoming_queue = incoming_queue

    def run(self):
        try:
            while True:
                msg_bytes = self.tcp_reader.receive()
                self.incoming_queue.put(parse_message(msg_bytes))
        except ConnectionResetError:
            print('loginserver(%s): disconnected' % self.my_id)

        self.incoming_queue.put(LoginServerDisconnectedMessage())
        print('loginserver(%s): signalled launcher; login server reader exiting' % self.my_id)


class LoginServerWriter():
    def __init__(self, my_id, sock, outgoing_queue):
        self.my_id = my_id
        self.tcp_writer = TcpMessageWriter(sock)
        self.outgoing_queue = outgoing_queue

    def run(self):
        while True:
            msg = self.outgoing_queue.get()
            if not isinstance(msg, LoginServerDisconnectedMessage):
                self.tcp_writer.send(msg.to_bytes())
            else:
                break

        print('loginserver(%s): writer exiting gracefully' % self.my_id)


def handle_login_server(login_server_config, incoming_queue, outgoing_queue):
    my_id = id(gevent.getcurrent())
    gevent.getcurrent().name = 'login_server_handler'

    success = False
    while not success:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = IPv4Address(socket.gethostbyname(login_server_config['host']))
            port = login_server_config['port']
            sock.connect((str(ip), port))
            print('loginserver(%s): connected to login server at %s:%s' % (my_id, ip, port))
            success = True
        except ConnectionRefusedError:
            sock.close()
            print('loginserver(%s): remote end is refusing connections. Reconnecting in 10 seconds...' % my_id)
            gevent.sleep(10)

    reader = LoginServerReader(my_id, sock, incoming_queue)
    gevent.spawn(reader.run)

    writer = LoginServerWriter(my_id, sock, outgoing_queue)
    writer.run()

    print('loginserver(%s): remote end disconnected.' % my_id)
