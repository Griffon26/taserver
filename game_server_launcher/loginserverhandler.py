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

from common.connectionhandler import *
from common.messages import parse_message_from_bytes
from ipaddress import IPv4Address


class LoginServerReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        return parse_message_from_bytes(msg_bytes)


class LoginServerWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class LoginServer(Peer):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port


class LoginServerHandler(OutgoingConnectionHandler):
    def __init__(self, config, incoming_queue):
        super().__init__('loginserver',
                         socket.gethostbyname(config['host']),
                         int(config['port']),
                         incoming_queue)
        self.logger.info('%s(%s): Connecting to login server at %s:%s...' %
                         (self.task_name, id(gevent.getcurrent()), config['host'], config['port']))

    def create_connection_instances(self, sock, address):
        reader = LoginServerReader(sock)
        writer = LoginServerWriter(sock)
        peer = LoginServer(IPv4Address(address[0]), int(address[1]))
        return reader, writer, peer


def handle_login_server(login_server_config, incoming_queue):
    login_server_handler = LoginServerHandler(login_server_config, incoming_queue)
    login_server_handler.run(retry_time=10)
