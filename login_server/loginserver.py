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

import gevent
import random
import string

from .datatypes import *
from .gameserverlauncherhandler import GameServer
from .player.player import Player
from .player.state.unauthenticated_state import UnauthenticatedState
from .protocol_errors import ProtocolViolationError
from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage


def first_unused_number_above(numbers, minimum):
    used_numbers = (n for n in numbers if n >= minimum)
    first_number_above = next(i for i, e in enumerate(sorted(used_numbers) + [None], start=minimum) if i != e)
    return first_number_above


class LoginServer:
    def __init__(self, server_queue, client_queues, authcode_queue, accounts, configuration):
        self.server_queue = server_queue
        self.client_queues = client_queues
        self.authcode_queue = authcode_queue

        self.game_servers = {}

        self.players = {}
        self.accounts = accounts
        self.message_handlers = {
            AuthCodeRequestMessage: self.handle_authcode_request_message,
            PeerConnectedMessage: self.handle_client_connected_message,
            PeerDisconnectedMessage: self.handle_client_disconnected_message,
            ClientMessage: self.handle_client_message,
            Launcher2LoginServerInfoMessage: self.handle_server_info_message,
        }

    def run(self):
        gevent.getcurrent().name = 'login_server'
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

    def send_all_on_server(self, data, game_server):
        for player in self.find_players_by(game_server=game_server):
            player.send(data)

    def handle_client_connected_message(self, msg):
        if isinstance(msg.peer, Player):
            unique_id = first_unused_number_above(self.players.keys(), 0x10000000)

            player = msg.peer
            player.unique_id = unique_id
            player.login_server = self
            player.set_state(UnauthenticatedState)
            self.players[unique_id] = player
        elif isinstance(msg.peer, GameServer):
            serverid1 = first_unused_number_above(self.game_servers.keys(), 1)

            game_server = msg.peer
            game_server.serverid1 = serverid1
            game_server.serverid2 = serverid1 + 0x10000000
            self.game_servers[serverid1] = game_server

            print('server: added game server %s' % game_server.ip)
        else:
            assert False, "Invalid connection message received"

    def handle_client_disconnected_message(self, msg):
        if isinstance(msg.peer, Player):
            player = msg.peer
            player.disconnect()
            del(self.players[player.unique_id])

        elif isinstance(msg.peer, GameServer):
            game_server = msg.peer
            print('server: removed game server %s (%s:%s)' % (game_server.serverid1,
                                                              game_server.ip,
                                                              game_server.port))
            game_server.disconnect()
            del (self.game_servers[game_server.serverid1])

        else:
            assert False, "Invalid disconnection message received"

    def handle_client_message(self, msg):
        current_player = msg.peer
        current_player.last_received_seq = msg.clientseq

        requests = '\n'.join(['  %04X' % req.ident for req in msg.requests])
        print('server: %s sent:\n%s' % (current_player, requests))

        for request in msg.requests:
            current_player.handle_request(request)

    def handle_server_info_message(self, msg):
        game_server = msg.peer
        game_server.set_info(msg.port, msg.description, msg.motd)
        print('server: server info received for server %s (%s:%s)' % (game_server.serverid1,
                                                                      game_server.ip,
                                                                      game_server.port))

