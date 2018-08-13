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

from gevent.server import StreamServer

from common.tcpmessage import TcpMessageReader, TcpMessageWriter
from common.messages import parse_message
from .launchermessages import GameControllerDisconnectedMessage


class GameControllerReader:
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
            print('gamecontroller(%s): disconnected' % self.my_id)

        self.incoming_queue.put(GameControllerDisconnectedMessage())
        print('gamecontroller(%s): signalled launcher; reader exiting' % self.my_id)


class GameControllerWriter:
    def __init__(self, my_id, sock, outgoing_queue):
        self.my_id = my_id
        self.tcp_writer = TcpMessageWriter(sock)
        self.outgoing_queue = outgoing_queue

    def run(self):
        while True:
            msg = self.outgoing_queue.get()
            if not isinstance(msg, GameControllerDisconnectedMessage):
                try:
                    self.tcp_writer.send(msg.to_bytes())
                except ConnectionResetError:
                    # Ignore a closed connection here. The reader will notice
                    # it and send us the DisconnectedMessage to tell us that
                    # we can close the socket and terminate
                    pass
            else:
                break

        self.tcp_writer.close()
        print('gamecontroller(%s): writer exiting gracefully' % self.my_id)


class GameControllerHandler:
    def __init__(self, config, incoming_queue, outgoing_queue):
        self.my_id = id(gevent.getcurrent())
        self.port = int(config['port'])
        self.incoming_queue = incoming_queue
        self.outgoing_queue = outgoing_queue

    def run(self):
        server = StreamServer(('127.0.0.1', self.port), self._handle, spawn = 1)
        server.serve_forever()

    def _handle(self, sock, address):
        print('gamecontroller(%s): connected' % self.my_id)

        reader = GameControllerReader(self.my_id, sock, self.incoming_queue)
        gevent.spawn(reader.run)

        writer = GameControllerWriter(self.my_id, sock, self.outgoing_queue)
        writer.run()


def handle_game_controller(game_controller_config, incoming_queue, outgoing_queue):
    game_controller_handler = GameControllerHandler(game_controller_config,
                                                    incoming_queue,
                                                    outgoing_queue)
    game_controller_handler.run()
