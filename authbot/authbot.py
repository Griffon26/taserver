#!/usr/bin/env python3
#
# Copyright (C) 2019  Maurice van der Pot <griffon26@kfk4ever.com>
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

import base64
from functools import wraps
import gevent
import inspect
import logging

from common.datatypes import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.loginprotocol import LoginProtocolMessage
from common.statetracer import statetracer, TracingDict

from .hirezloginserverhandler import HirezLoginServer


def handles(packet):
    """
    A decorator that defines a function as a handler for a certain packet
    :param packet: the packet being handled by the function
    """

    def real_decorator(func):
        func.handles_packet = packet

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return real_decorator


@statetracer()
class AuthBot:
    def __init__(self, config, incoming_queue):
        gevent.getcurrent().name = 'authbot'

        self.logger = logging.getLogger(__name__)
        self.incoming_queue = incoming_queue
        self.login_server = None
        self.login_name = config['login_name']
        self.display_name = None
        password_hash = base64.b64decode(config['password_hash'])

        self.message_handlers = {
            PeerConnectedMessage: self.handle_peer_connected,
            PeerDisconnectedMessage: self.handle_peer_disconnected,
            LoginProtocolMessage: self.handle_login_protocol_message
        }

    def run(self):
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def handle_peer_connected(self, msg):
        assert isinstance(msg.peer, HirezLoginServer)
        assert self.login_server is None
        self.logger.info('authbot: hirez login server connected')
        self.login_server = msg.peer
        self.login_server.send(
            a01bc().set([
                m049e(),
                m0489()
            ])
        )

    def handle_peer_disconnected(self, msg):
        assert isinstance(msg.peer, HirezLoginServer)
        assert self.login_server is msg.peer
        msg.peer.disconnect()
        self.logger.info('authbot: hirez login server disconnected')

    def handle_login_protocol_message(self, msg):
        msg.peer.last_received_seq = msg.clientseq

        requests = ' '.join(['%04X' % req.ident for req in msg.requests])
        self.logger.info('authbot: login server sent: %s' % requests)

        for request in msg.requests:
            methods = [
                func for name, func in inspect.getmembers(self) if
                getattr(func, 'handles_packet', None) == type(request)
            ]
            if not methods:
                self.logger.warning("No handler found for request %s" % request)
                return

            if len(methods) > 1:
                raise ValueError("Duplicate handlers found for request")

            methods[0](request)

    @handles(packet=a01bc)
    def handle_a01bc(self, request):
        pass

    @handles(packet=a0197)
    def handle_a0197(self, request):
        self.login_server.send(a003a())

    @handles(packet=a003a)
    def handle_a003a(self, request):
        salt = request.findbytype(m03e3).value
        self.login_server.send(
            a003a().set([
                m0056(),
                m0494().set(self.login_name),
                m0671(),
                m0671(),
                m0672(),
                m0673(),
                m0677(),
                m0676(),
                m0674(),
                m0675(),
                m0434(),
                m049e()
            ])
        )

    @handles(packet=a003d)
    def handle_a003d(self, request):
        self.display_name = request.findbytype(m034a).value

    @handles(packet=a0070)
    def handle_chat(self, request):
        assert self.display_name is not None

        message_type = request.findbytype(m009e).value
        message_text = request.findbytype(m02e6).value
        sender_name = request.findbytype(m02fe).value

        if message_type == MESSAGE_PRIVATE and sender_name != self.display_name:
            self.login_server.send(
                a0070().set([
                    m009e().set(MESSAGE_PRIVATE),
                    m02e6().set('hey there %s, how are you doing?' % sender_name),
                    m034a().set(sender_name),
                    m0574()
                ])
            )

def handle_authbot(config, incoming_queue):
    authbot = AuthBot(config, incoming_queue)
    # launcher.trace_as('authbot')
    authbot.run()
