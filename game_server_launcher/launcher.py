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

from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from .gamecontrollerhandler import GameController
from .loginserverhandler import LoginServer

class Launcher:
    def __init__(self, game_server_config, incoming_queue):
        self.game_server_config = game_server_config
        self.incoming_queue = incoming_queue
        self.players = {}
        self.game_controller = None
        self.login_server = None

        self.message_handlers = {
            PeerConnectedMessage : self.handle_peer_connected,
            PeerDisconnectedMessage : self.handle_peer_disconnected,
            Login2LauncherNextMapMessage : self.handle_next_map_message,
            Login2LauncherSetPlayerLoadoutsMessage : self.handle_set_player_loadouts_message,
            Login2LauncherRemovePlayerLoadoutsMessage : self.handle_remove_player_loadouts_message,
            Game2LauncherTeamSwitchMessage : self.handle_team_switch_message,
            Game2LauncherMatchTimeMessage : self.handle_match_time_message,
            Game2LauncherLoadoutRequest : self.handle_loadout_request_message,
        }

    def run(self):
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def handle_peer_connected(self, msg):
        if isinstance(msg.peer, GameController):
            if self.game_controller is not None:
                raise RuntimeError('There should only be one game controller at a time')
            self.game_controller = msg.peer

        elif isinstance(msg.peer, LoginServer):
            if self.login_server is not None:
                raise RuntimeError('There should only be a connection to one login server at a time')
            self.login_server = msg.peer

            msg = Launcher2LoginServerInfoMessage(int(self.game_server_config['port']),
                                                  self.game_server_config['description'],
                                                  self.game_server_config['motd'])
            self.login_server.send(msg)

        else:
            assert False, "Invalid connection message received"

    def handle_peer_disconnected(self, msg):
        if isinstance(msg.peer, GameController):
            if self.game_controller is None:
                raise RuntimeError('How can a game controller disconnect if it\'s not there?')
            self.game_controller.disconnect()
            self.game_controller = None
        elif isinstance(msg.peer, LoginServer):
            if self.login_server is None:
                raise RuntimeError('How can a login server disconnect if it\'s not there?')
            self.login_server.disconnect()
            self.login_server = None
        else:
            assert False, "Invalid disconnection message received"

    def handle_next_map_message(self, msg):
        raise NotImplementedError

    def handle_set_player_loadouts_message(self, msg):
        print('launcher: loadouts changed for player 0x%08X' % msg.unique_id)
        self.players[msg.unique_id] = msg.loadouts

    def handle_remove_player_loadouts_message(self, msg):
        print('launcher: loadouts removed for player 0x%08X' % msg.unique_id)
        del(self.players[msg.unique_id])

    def handle_team_switch_message(self, msg):
        raise NotImplementedError

    def handle_match_time_message(self, msg):
        raise NotImplementedError

    def handle_loadout_request_message(self, msg):
        if msg.player_unique_id not in self.players:
            print('launcher: Unable to find player 0x%08X\'s loadouts. Ignoring request.' % msg.player_unique_id)
            return

        # Class and loadout keys are strings because they came in as json.
        # There's not much point in converting all keys in the loadouts
        # dictionary from strings back to ints if we are just going to
        # send it out as json again later.
        player_key = msg.player_unique_id
        class_key = str(msg.class_id)
        loadout_key = str(msg.loadout_number)

        msg = Launcher2GameLoadoutMessage(self.players[player_key][class_key][loadout_key])
        self.game_controller.send(msg)


def handle_launcher(game_server_config, incoming_queue):
    launcher = Launcher(game_server_config, incoming_queue)
    launcher.run()