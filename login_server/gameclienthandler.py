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
from .player.player import Player
from common.token_bucket import TokenBucketPool


class GameClientHandler(IncomingConnectionHandler):
    def __init__(self, incoming_queue, dump_queue, data_root):
        super().__init__('gameclient',
                         '0.0.0.0',
                         9000,
                         incoming_queue)
        self.dump_queue = dump_queue
        self.data_root = data_root
        self.token_bucket_data_pool = TokenBucketPool(10000, 60, 'bytes') # 10KB/min per IP
        self.token_bucket_msgs_pool = TokenBucketPool(100, 60, 'messages') # 100msgs/min per IP

    def create_connection_instances(self, sock, address):
        reader = LoginProtocolReader(sock, self.dump_queue,
                                     token_bucket_data=self.token_bucket_data_pool.get(address[0]),
                                     token_bucket_msgs=self.token_bucket_msgs_pool.get(address[0]))
        writer = LoginProtocolWriter(sock, self.dump_queue)
        peer = Player(address, self.data_root)
        return reader, writer, peer


def handle_game_client(incoming_queue, dump_queue, data_root):
    game_client_handler = GameClientHandler(incoming_queue, dump_queue, data_root)
    game_client_handler.run()
