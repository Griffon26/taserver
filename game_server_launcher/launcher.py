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

from common.errors import FatalError
from common.firewall import reset_firewall, modify_firewall
from common.ipaddresspair import IPAddressPair
from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.statetracer import statetracer, TracingDict
from common import versions
from .gamecontrollerhandler import GameController
from .gameserverhandler import StartGameServerMessage, StopGameServerMessage, GameServerTerminatedMessage
from .loginserverhandler import LoginServer

game_server_ports = [7777, 7778]


def get_other_port(port):
    for other_port in game_server_ports:
        if other_port != port:
            return other_port
    assert(False)


class IncompatibleVersionError(FatalError):
    def __init__(self, message):
        super().__init__('A version incompatibility was found: %s' % message)


@statetracer('address_pair', 'players')
class Launcher:
    def __init__(self, game_server_config, incoming_queue, server_handler_queue):
        gevent.getcurrent().name = 'launcher'

        self.logger = logging.getLogger(__name__)
        self.game_server_config = game_server_config
        self.incoming_queue = incoming_queue
        self.server_handler_queue = server_handler_queue
        self.players = TracingDict()
        self.game_controller = None
        self.login_server = None

        self.active_server_port = None
        self.pending_server_port = None
        self.server_stopping = False
        self.controller_context = {}

        self.last_server_info_message = None
        self.last_map_info_message = None
        self.last_team_info_message = None
        self.last_score_info_message = None
        self.last_match_time_message = None
        self.last_server_ready_message = None
        self.last_match_end_message = None

        self.address_pair, errormsg = IPAddressPair.detect()

        if not self.address_pair.external_ip:
            self.logger.warning('Unable to detect public IP address: %s\n'
                                'This will cause problems if the login server '
                                'or any of your players are not on your LAN.' % errormsg)
        else:
            self.logger.info('launcher: detected external IP: %s' % self.address_pair.external_ip)

        if not self.address_pair.internal_ip:
            self.logger.warning('You appear to be running the game server on a machine '
                                'directly connected to the internet. This is will cause '
                                'problems if the login server or any of your players '
                                'are on your LAN.')
        else:
            self.logger.info('launcher: detected internal IP: %s' % self.address_pair.internal_ip)

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
            Game2LauncherServerInfoMessage: self.handle_server_info_message,
            Game2LauncherMapInfoMessage: self.handle_map_info_message,
            Game2LauncherTeamInfoMessage: self.handle_team_info_message,
            Game2LauncherScoreInfoMessage: self.handle_score_info_message,
            Game2LauncherMatchTimeMessage: self.handle_match_time_message,
            Game2LauncherMatchEndMessage: self.handle_match_end_message,
            Game2LauncherLoadoutRequest: self.handle_loadout_request_message,
            GameServerTerminatedMessage: self.handle_game_server_terminated_message,
        }

    def run(self):
        reset_firewall('whitelist')
        self.pending_server_port = game_server_ports[0]
        self.server_handler_queue.put(StartGameServerMessage(self.pending_server_port))
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def handle_peer_connected(self, msg):
        if isinstance(msg.peer, GameController):
            pass

        elif isinstance(msg.peer, LoginServer):
            if self.login_server is not None:
                raise RuntimeError('There should only be a connection to one login server at a time')
            self.login_server = msg.peer

            msg = Launcher2LoginProtocolVersionMessage(str(versions.launcher2loginserver_protocol_version))
            self.login_server.send(msg)

            msg = Launcher2LoginAddressInfoMessage(
                str(self.address_pair.external_ip) if self.address_pair.external_ip else '',
                str(self.address_pair.internal_ip) if self.address_pair.internal_ip else '')
            self.login_server.send(msg)

            # Send the latest relevant information that was received
            # while the login server was not connected
            if self.last_server_info_message:
                self.login_server.send(self.last_server_info_message)
                self.last_server_info_message = None
            if self.last_map_info_message:
                self.login_server.send(self.last_map_info_message)
                self.last_map_info_message = None
            if self.last_team_info_message:
                self.login_server.send(self.last_team_info_message)
                self.last_team_info_message = None
            if self.last_score_info_message:
                self.login_server.send(self.last_score_info_message)
                self.last_score_info_message = None
            if self.last_match_time_message:
                self.login_server.send(self.last_match_time_message)
                self.last_match_time_message = None
            if self.last_server_ready_message:
                self.login_server.send(self.last_server_ready_message)
                self.last_server_ready_message = None
            if self.last_match_end_message:
                self.login_server.send(self.last_match_end_message)
                self.last_match_end_message = None

        else:
            assert False, "Invalid connection message received"

    def hash_server_password(self, password: str) -> List[int]:
        hash_constants = [0x55, 0x93, 0x55, 0x58, 0xBA, 0x6f, 0xe9, 0xf9]
        interspersed_constants = [0x7a, 0x1e, 0x9f, 0x47, 0xf9, 0x17, 0xb0, 0x03]
        result = []
        for idx, c in enumerate(password.encode('latin1')):
            pattern_idx = idx % 8
            result.extend([(c ^ hash_constants[pattern_idx]), interspersed_constants[pattern_idx]])

        return result

    def handle_peer_disconnected(self, msg):
        if isinstance(msg.peer, GameController):
            msg.peer.disconnect()
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
        self.logger.info('launcher: switching to new server instance on port %d' % self.pending_server_port)
        if self.active_server_port:
            self.server_handler_queue.put(StopGameServerMessage(self.active_server_port))
            self.server_stopping = True

        self.active_server_port = self.pending_server_port

    def handle_set_player_loadouts_message(self, msg):
        self.logger.info('launcher: loadouts changed for player %d' % msg.unique_id)
        self.players[msg.unique_id] = msg.loadouts

    def handle_remove_player_loadouts_message(self, msg):
        self.logger.info('launcher: loadouts removed for player %d' % msg.unique_id)
        del(self.players[msg.unique_id])

    def handle_add_player_message(self, msg):
        if msg.ip:
            self.logger.info('launcher: login server added player %d with ip %s' % (msg.unique_id, msg.ip))
            modify_firewall('whitelist', 'add', msg.unique_id, msg.ip)
        else:
            self.logger.info('launcher: login server added local player %d' % msg.unique_id)

    def handle_remove_player_message(self, msg):
        if msg.ip:
            self.logger.info('launcher: login server removed player %d with ip %s' % (msg.unique_id, msg.ip))
            modify_firewall('whitelist', 'remove', msg.unique_id, msg.ip)
        else:
            self.logger.info('launcher: login server removed local player %d' % msg.unique_id)

    def handle_pings_message(self, msg):
        if self.game_controller:
            self.game_controller.send(Launcher2GamePings(msg.player_pings))

    def handle_game_controller_protocol_version_message(self, msg):
        controller_version = StrictVersion(msg.version)
        my_version = versions.launcher2controller_protocol_version

        self.logger.info('launcher: received protocol version %s from game controller' % controller_version)

        if controller_version.version[0] != my_version.version[0]:
            raise IncompatibleVersionError('The protocol version of the game controller DLL (%s) is incompatible '
                                           'with the version supported by this game server launcher (%s)' %
                                           (controller_version,
                                            my_version))

        self.game_controller = msg.peer
        msg = Launcher2GameInit(self.controller_context)
        self.game_controller.send(msg)

    def handle_server_info_message(self, msg):
        self.logger.info('launcher: received server info from game controller')

        msg = Launcher2LoginServerInfoMessage(msg.description,
                                              msg.motd,
                                              msg.game_setting_mode,
                                              msg.password_hash)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_server_info_message = msg

    def handle_map_info_message(self, msg):
        self.logger.info('launcher: received map info from game controller')

        msg = Launcher2LoginMapInfoMessage(msg.map_id)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_map_info_message = msg

    def handle_team_info_message(self, msg):
        self.logger.info('launcher: received team info from game controller')

        for player_id, team_id in msg.player_to_team_id.items():
            if int(player_id) not in self.players:
                return

        msg = Launcher2LoginTeamInfoMessage(msg.player_to_team_id)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_team_info_message = msg

    def handle_score_info_message(self, msg):
        self.logger.info('launcher: received score info from game controller')

        msg = Launcher2LoginScoreInfoMessage(msg.be_score, msg.ds_score)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_score_info_message = msg

    def handle_match_time_message(self, msg):
        self.logger.info('launcher: received match time from game controller')

        msg = Launcher2LoginMatchTimeMessage(msg.seconds_remaining, msg.counting)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_match_time_message = msg

        if self.pending_server_port != self.active_server_port:
            msg = Launcher2LoginServerReadyMessage(self.pending_server_port)
            if self.login_server:
                self.login_server.send(msg)
            else:
                self.last_server_ready_message = msg

    def handle_match_end_message(self, msg):
        self.logger.info('launcher: received match end from game controller (controller context = %s)' % msg.controller_context)

        self.game_controller = None
        self.controller_context = msg.controller_context

        msg = Launcher2LoginMatchEndMessage()
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_match_end_message = msg

        self.pending_server_port = get_other_port(self.active_server_port)
        self.server_handler_queue.put(StartGameServerMessage(self.pending_server_port))

    def handle_loadout_request_message(self, msg):
        self.logger.info('launcher: received loadout request from game controller')

        # Class and loadout keys are strings because they came in as json.
        # There's not much point in converting all keys in the loadouts
        # dictionary from strings back to ints if we are just going to
        # send it out as json again later.
        player_key = msg.player_unique_id
        class_key = str(msg.class_id)
        loadout_key = str(msg.loadout_number)

        if msg.player_unique_id in self.players:
            loadout = self.players[player_key][class_key][loadout_key]
        else:
            self.logger.warning('launcher: Unable to find player %d\'s loadouts. Sending empty loadout.' % msg.player_unique_id)
            loadout = {}

        msg = Launcher2GameLoadoutMessage(msg.player_unique_id,
                                          msg.class_id,
                                          loadout)
        self.game_controller.send(msg)

    def handle_game_server_terminated_message(self, msg):
        if self.server_stopping:
            self.logger.info('launcher: game server process terminated.')
            self.server_stopping = False
        else:
            self.pending_server_port = get_other_port(self.active_server_port)
            self.active_server_port = None
            self.logger.info('launcher: game server process terminated unexpectedly. Starting a new one on port %d.' %
                             self.pending_server_port)
            self.server_handler_queue.put(StartGameServerMessage(self.pending_server_port))

            msg = Launcher2LoginServerReadyMessage(None)
            if self.login_server:
                self.login_server.send(msg)
            else:
                self.last_server_ready_message = msg



def handle_launcher(game_server_config, incoming_queue, server_handler_queue):
    launcher = Launcher(game_server_config, incoming_queue, server_handler_queue)
    # launcher.trace_as('launcher')
    launcher.run()
