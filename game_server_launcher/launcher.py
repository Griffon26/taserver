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

from common.firewall import reset_firewall, modify_firewall
from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common import versions
from .gamecontrollerhandler import GameController
from .loginserverhandler import LoginServer


class IncompatibleVersionError(Exception):
    pass


class Launcher:
    def __init__(self, game_server_config, incoming_queue):
        gevent.getcurrent().name = 'launcher'

        self.game_server_config = game_server_config
        self.incoming_queue = incoming_queue
        self.players = {}
        self.game_controller = None
        self.login_server = None

        self.last_team_info_message = None
        self.last_score_info_message = None
        self.last_match_time_message = None
        self.last_match_end_message = None

        self.message_handlers = {
            PeerConnectedMessage: self.handle_peer_connected,
            PeerDisconnectedMessage: self.handle_peer_disconnected,
            Login2LauncherProtocolVersionMessage: self.handle_login_server_protocol_version_message,
            Login2LauncherNextMapMessage: self.handle_next_map_message,
            Login2LauncherSetPlayerLoadoutsMessage: self.handle_set_player_loadouts_message,
            Login2LauncherRemovePlayerLoadoutsMessage: self.handle_remove_player_loadouts_message,
            Login2LauncherAddPlayer: self.handle_add_player_message,
            Login2LauncherRemovePlayer: self.handle_remove_player_message,
            Login2LauncherPings: self.handle_pings_message,
            Game2LauncherProtocolVersionMessage: self.handle_game_controller_protocol_version_message,
            Game2LauncherTeamInfoMessage: self.handle_team_info_message,
            Game2LauncherScoreInfoMessage: self.handle_score_info_message,
            Game2LauncherMatchTimeMessage: self.handle_match_time_message,
            Game2LauncherMatchEndMessage: self.handle_match_end_message,
            Game2LauncherLoadoutRequest: self.handle_loadout_request_message,
        }

    def run(self):
        reset_firewall('whitelist')
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

            msg = Launcher2LoginProtocolVersionMessage(str(versions.launcher2loginserver_protocol_version))
            self.login_server.send(msg)

            msg = Launcher2LoginServerInfoMessage(int(self.game_server_config['port']),
                                                  self.game_server_config['description'],
                                                  self.game_server_config['motd'])
            self.login_server.send(msg)

            # Send the latest relevant information that was received while the login server was not connected
            if self.last_team_info_message:
                self.login_server.send(self.last_team_info_message)
                self.last_team_info_message = None
            if self.last_score_info_message:
                self.login_server.send(self.last_score_info_message)
                self.last_score_info_message = None
            if self.last_match_time_message:
                self.login_server.send(self.last_match_time_message)
                self.last_match_time_message = None
            if self.last_match_end_message:
                self.login_server.send(self.last_match_end_message)
                self.last_match_end_message = None

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

    def handle_login_server_protocol_version_message(self, msg):
        # The only time we get a message with the login server's protocol version
        # is when the version that we sent is incompatible with it.
        raise IncompatibleVersionError('The protocol version that this game server launcher supports (%s) is '
                                       'incompatible with the version supported by the login server at %s:%d (%s)' %
                                       (versions.launcher2loginserver_protocol_version,
                                        self.login_server.ip,
                                        self.login_server.port,
                                        StrictVersion(msg.version)))

    def handle_next_map_message(self, msg):
        self.game_controller.send(Launcher2GameNextMapMessage())

    def handle_set_player_loadouts_message(self, msg):
        print('launcher: loadouts changed for player 0x%08X' % msg.unique_id)
        self.players[msg.unique_id] = msg.loadouts

    def handle_remove_player_loadouts_message(self, msg):
        print('launcher: loadouts removed for player 0x%08X' % msg.unique_id)
        del(self.players[msg.unique_id])

    def handle_add_player_message(self, msg):
        modify_firewall('whitelist', 'add', msg.ip)

    def handle_remove_player_message(self, msg):
        modify_firewall('whitelist', 'remove', msg.ip)

    def handle_pings_message(self, msg):
        if self.game_controller:
            self.game_controller.send(Launcher2GamePings(msg.player_pings))

    def handle_game_controller_protocol_version_message(self, msg):
        controller_version = StrictVersion(msg.version)
        my_version = versions.launcher2controller_protocol_version

        if controller_version.version[0] != my_version.version[0]:
            raise IncompatibleVersionError('The protocol version of the game controller DLL (%s) is incompatible '
                                           'with the version supported by this game server launcher (%s)' %
                                           (controller_version,
                                            my_version))

    def handle_team_info_message(self, msg):
        for player_id, team_id in msg.player_to_team_id.items():
            assert int(player_id) in self.players

        msg = Launcher2LoginTeamInfoMessage(msg.player_to_team_id)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_team_info_message = msg

    def handle_score_info_message(self, msg):
        msg = Launcher2LoginScoreInfoMessage(msg.be_score, msg.ds_score)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_score_info_message = msg

    def handle_match_time_message(self, msg):
        msg = Launcher2LoginMatchTimeMessage(msg.seconds_remaining, msg.counting)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_match_time_message = msg

    def handle_match_end_message(self, msg):
        msg = Launcher2LoginMatchEndMessage()
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_match_end_message = msg

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

        msg = Launcher2GameLoadoutMessage(msg.player_unique_id,
                                          msg.class_id,
                                          self.players[player_key][class_key][loadout_key])
        self.game_controller.send(msg)


def handle_launcher(game_server_config, incoming_queue):
    launcher = Launcher(game_server_config, incoming_queue)
    launcher.run()
