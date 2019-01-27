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

from distutils.version import StrictVersion
import gevent
import logging
from gevent import socket
import urllib.request as urlreq

from common.errors import FatalError
from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.statetracer import statetracer, TracingDict

from .hirezloginserverhandler import HirezLoginServer


@statetracer()
class AuthBot:
    def __init__(self, incoming_queue):
        gevent.getcurrent().name = 'authbot'

        self.logger = logging.getLogger(__name__)
        self.incoming_queue = incoming_queue

        self.message_handlers = {
            PeerConnectedMessage: self.handle_peer_connected,
            PeerDisconnectedMessage: self.handle_peer_disconnected,
            #ClientMessage: self.handle_client_message
        }

    def run(self):
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def handle_peer_connected(self, msg):
        assert isinstance(msg.peer, HirezLoginServer)
        self.logger.info('authbot: hirez login server connected')

    def handle_peer_disconnected(self, msg):
        assert isinstance(msg.peer, HirezLoginServer)
        msg.peer.disconnect()
        self.logger.info('authbot: hirez login server disconnected')

    def handle_client_message(self, msg):
        self.logger.info('launcher: received client message')
        #msg.peer.send(msg)


def handle_authbot(incoming_queue):
    authbot = AuthBot(incoming_queue)
    # launcher.trace_as('authbot')
    authbot.run()
