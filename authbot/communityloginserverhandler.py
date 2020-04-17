#!/usr/bin/env python3
#
# Copyright (C) 2020  Maurice van der Pot <griffon26@kfk4ever.com>
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


class CommunityLoginServerReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        return parse_message_from_bytes(msg_bytes)


class CommunityLoginServerWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class CommunityLoginServer(Peer):
    pass


class CommunityLoginServerHandler(OutgoingConnectionHandler):
    def __init__(self, ports, incoming_queue):
        super().__init__('communityloginserver',
                         '127.0.0.1',
                         ports['authchannel'],
                         incoming_queue)
        self.logger.info('%s(%s): Connecting to community login server on localhost:%s...' %
                         (self.task_name, id(gevent.getcurrent()), ports['authchannel']))

    def create_connection_instances(self, sock, address):
        reader = CommunityLoginServerReader(sock)
        writer = CommunityLoginServerWriter(sock)
        peer = CommunityLoginServer()
        return reader, writer, peer


def handle_community_login_server(ports, incoming_queue):
    hirez_login_server_handler = CommunityLoginServerHandler(ports, incoming_queue)
    hirez_login_server_handler.run(retry_time=10)
