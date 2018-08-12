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

import random
import string

from .datatypes import *
from .player.player import Player
from .player.state.unauthenticated_state import UnauthenticatedState
from .protocol_errors import ProtocolViolationError
from .server_info import ServerInfo
from common.messages import *


class Server:
    def __init__(self, server_queue, client_queues, authcode_queue, accounts, configuration):
        self.server_queue = server_queue
        self.client_queues = client_queues
        self.authcode_queue = authcode_queue

        self.game_servers = {}

        self.players = {}
        self.accounts = accounts
        self.message_handlers = {
            AuthCodeRequestMessage: self.handle_authcode_request_message,
            ClientConnectedMessage: self.handle_client_connected_message,
            ClientDisconnectedMessage: self.handle_client_disconnected_message,
            ClientMessage: self.handle_client_message,
            GameServerConnectedMessage: self.handle_game_server_connected_message,
            GameServerDisconnectedMessage: self.handle_game_server_disconnected_message,
            Launcher2LoginServerInfoMessage: self.handle_server_info_message,
        }

    def run(self):
        while True:
            for message in self.server_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def find_server_by_id1(self, id1):
        for game_server in self.game_servers.values():
            if game_server.serverid1 == id1:
                return game_server
        raise ProtocolViolationError('No server found with specified serverid1')

    def find_server_by_id2(self, id2):
        for game_server in self.game_servers.values():
            if game_server.serverid2 == id2:
                return game_server
        raise ProtocolViolationError('No server found with specified serverid2')

    def find_player_by(self, **kwargs):
        matching_players = self.find_players_by(**kwargs)

        if len(matching_players) == 0:
            raise ValueError("No player matched query")

        if len(matching_players) > 1:
            raise ValueError("More than one player matched query")
        return matching_players[0]

    def find_players_by(self, **kwargs):
        matching_players = self.players.values()
        for key, val in kwargs.items():
            matching_players = [player for player in matching_players if getattr(player, key) == val]

        return matching_players

    def handle_authcode_request_message(self, msg):
        availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
        authcode = ''.join([random.choice(availablechars) for i in range(8)])
        print('server: authcode requested for %s, returned %s' % (msg.login_name, authcode))
        self.accounts.add_account(msg.login_name, authcode)
        self.accounts.save()
        self.authcode_queue.put((msg.login_name, authcode))

    def handle_client_disconnected_message(self, msg):
        print('server: client(%s)\'s reader quit; stopping writer' % msg.clientid)
        self.client_queues[msg.clientid].put((None, None))
        del (self.client_queues[msg.clientid])

        # Remove and don't complain if it wasn't there yet
        self.players.pop(msg.clientid, None)

    def send_all_on_server(self, data, game_server):
        for player in self.find_players_by(game_server=game_server):
            player.send(data)

    def handle_client_connected_message(self, msg):
        offset_for_temp_ids = 0x10000000
        used_slots = {player.slot for player in self.players.items()}
        free_slot = next(i for i, e in enumerate(sorted(used_slots) + [None], start = 1) if i != e)
        unique_id = free_slot + offset_for_temp_ids

        player = Player(msg.clientid, unique_id, msg.clientaddress, msg.clientport, login_server=self)
        player.set_state(UnauthenticatedState)
        self.players[msg.clientid] = player

    def handle_client_message(self, msg):
        current_player = self.players[msg.clientid]
        current_player.last_received_seq = msg.clientseq

        requests = '\n'.join(['  %04X' % req.ident for req in msg.requests])
        print('server: client(%s) sent:\n%s' % (current_player, requests))

        for request in msg.requests:
            current_player.handle_request(request)

    def handle_game_server_connected_message(self, msg):
        print('server: added game server %s' % msg.game_server_id)
        self.game_servers[msg.game_server_id] = ServerInfo(1, 2, msg.game_server_ip, msg.game_server_queue)

    def handle_game_server_disconnected_message(self, msg):
        server = self.game_servers[msg.game_server_id]
        print('server: removed game server %s (%s:%s)' % (msg.game_server_id,
                                                          server.ip,
                                                          server.port))
        del(self.game_servers[msg.game_server_id])

    def handle_server_info_message(self, msg):
        server = self.game_servers[msg.game_server_id]
        server.set_info(msg.port, msg.description, msg.motd)
        print('server: server info received for server %s (%s:%s)' % (msg.game_server_id,
                                                                      server.ip,
                                                                      server.port))

