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
from common.loginprotocol import LoginProtocolReader, LoginProtocolWriter
from ipaddress import IPv4Address


class HirezLoginServer(Peer):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.last_received_seq = None

    def send(self, data):
        super().send((data, self.last_received_seq))


class HirezLoginServerHandler(OutgoingConnectionHandler):
    def __init__(self, config, ports, incoming_queue):
        super().__init__('hirezloginserver',
                         socket.gethostbyname(config['hirez_login_server']),
                         ports['client2login'],
                         incoming_queue)
        self.logger.info('%s(%s): Connecting to HiRez login server at %s:%s...' %
                         (self.task_name, id(gevent.getcurrent()),
                          config['hirez_login_server'], ports['client2login']))

    def create_connection_instances(self, sock, address):
        reader = LoginProtocolReader(sock, None)
        writer = LoginProtocolWriter(sock, None)
        peer = HirezLoginServer(IPv4Address(address[0]), int(address[1]))
        return reader, writer, peer


def handle_hirez_login_server(hirez_login_server_config, ports, incoming_queue):
    hirez_login_server_handler = HirezLoginServerHandler(hirez_login_server_config, ports, incoming_queue)
    hirez_login_server_handler.run(retry_time=10)
