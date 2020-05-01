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
from common import utils
from common.datatypes import *
from .player.friends import Friends


class AuthCodeReader(TcpMessageConnectionReader):
    def decode(self, msg_bytes):
        return parse_message_from_bytes(msg_bytes)


class AuthCodeWriter(TcpMessageConnectionWriter):
    def encode(self, msg):
        return msg.to_bytes()


class AuthBot:
    def __init__(self, peer):
        self.peer = peer
        self.login_name = 'taserverbot'
        self.display_name = 'taserverbot'
        self.game_server = None
        self.unique_id = utils.AUTHBOT_ID
        self.verified = True
        self.friends = Friends(self)

    def send(self, msg):
        # Ignore anything that would normally be sent from the login server to the client
        pass


class AuthCodeRequester(Peer):
    def __init__(self):
        super().__init__()
        self.authbot = AuthBot(self)


class AuthCodeHandler(IncomingConnectionHandler):
    def __init__(self, incoming_queue):
        super().__init__('authcodehandler',
                         '127.0.0.1',
                         9800,
                         incoming_queue)

    def create_connection_instances(self, sock, address):
        reader = AuthCodeReader(sock)
        writer = AuthCodeWriter(sock)
        peer = AuthCodeRequester()
        return reader, writer, peer


def handle_authcodes(incoming_queue):
    auth_code_handler = AuthCodeHandler(incoming_queue)
    auth_code_handler.run()
