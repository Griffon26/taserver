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
import os

from common.errors import FatalError
from common.firewall import FirewallClient
from common.ipaddresspair import IPAddressPair
from common.messages import *
from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.statetracer import statetracer, TracingDict
from common.pendingcallbacks import PendingCallbacks, ExecuteCallbackMessage
from common import versions
from .gamecontrollerhandler import GameController
from .gameserverhandler import StartGameServerMessage, StopGameServerMessage, \
                                FreezeGameServerMessage, UnfreezeGameServerMessage, \
                                GameServerTerminatedMessage
from .loginserverhandler import LoginServer


class GameServerProcess:
    def __init__(self, name, ports, server_handler_queue):
        self.name = name
        self.port = ports[name]
        self.server_handler_queue = server_handler_queue
        self.running = False
        self.ready = False
        self.frozen = False
        self.stopping = False

    def start(self):
        self.server_handler_queue.put(StartGameServerMessage(self.name))
        self.running = True
        self.ready = False

    def stop(self):
        self.server_handler_queue.put(StopGameServerMessage(self.name))
        self.stopping = True

    def freeze(self):
        self.server_handler_queue.put(FreezeGameServerMessage(self.name))
        self.frozen = True

    def unfreeze(self):
        self.server_handler_queue.put(UnfreezeGameServerMessage(self.name))
        self.frozen = False

    def set_ready(self, ready):
        self.ready = ready

    def terminated(self):
        self.running = False
        self.ready = False
        self.frozen = False
        self.stopping = False


class IncompatibleVersionError(FatalError):
    def __init__(self, message):
        super().__init__('A version incompatibility was found: %s' % message)


@statetracer('address_pair', 'players')
class Launcher:
    def __init__(self, game_server_config, shared_config, ports, incoming_queue, server_handler_queue, data_root):
        gevent.getcurrent().name = 'launcher'

        self.pending_callbacks = PendingCallbacks(incoming_queue)

        self.logger = logging.getLogger(__name__)
        self.ports = ports
        self.firewall = FirewallClient(ports, shared_config)
        self.game_server_config = game_server_config
        self.incoming_queue = incoming_queue
        self.server_handler_queue = server_handler_queue
        self.players = TracingDict()
        self.game_controller = None
        self.login_server = None

        self.active_server = GameServerProcess('gameserver1', self.ports, server_handler_queue)
        self.pending_server = GameServerProcess('gameserver2', self.ports, server_handler_queue)
        self.min_next_switch_time = None

        self.map_rotation_state_path = os.path.join(data_root, 'maprotationstate.json')
        try:
            with open(self.map_rotation_state_path, 'rt') as f:
                self.controller_context = json.load(f)
        except IOError:
            self.controller_context = {}

        self.last_waiting_for_map_message = None
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
            Login2LauncherMapVoteResult: self.handle_map_vote_result,
            Game2LauncherProtocolVersionMessage: self.handle_game_controller_protocol_version_message,
            Game2LauncherServerInfoMessage: self.handle_server_info_message,
            Game2LauncherMapInfoMessage: self.handle_map_info_message,
            Game2LauncherTeamInfoMessage: self.handle_team_info_message,
            Game2LauncherScoreInfoMessage: self.handle_score_info_message,
            Game2LauncherMatchTimeMessage: self.handle_match_time_message,
            Game2LauncherMatchEndMessage: self.handle_match_end_message,
            Game2LauncherLoadoutRequest: self.handle_loadout_request_message,
            GameServerTerminatedMessage: self.handle_game_server_terminated_message,
            ExecuteCallbackMessage: self.handle_execute_callback_message
        }

    def run(self):
        self.firewall.reset_firewall('whitelist')
        self.pending_server.start()
        while True:
            for message in self.incoming_queue:
                handler = self.message_handlers[type(message)]
                handler(message)

    def get_other_server(self, server):
        for other_server in ['gameserver1', 'gameserver2']:
            if other_server != server:
                return other_server
        assert False

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
            if self.last_waiting_for_map_message:
                self.login_server.send(self.last_waiting_for_map_message)
                self.last_waiting_for_map_message = None
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

    def handle_execute_callback_message(self, msg):
        callback_id = msg.callback_id
        self.pending_callbacks.execute(callback_id)

    def handle_login_server_protocol_version_message(self, msg):
        # The only time we get a message with the login server's protocol version
        # is when the version that we sent is incompatible with it.
        raise IncompatibleVersionError('The protocol version that this game server launcher supports (%s) is '
                                       'incompatible with the version supported by the login server at %s:%d (%s)' %
                                       (versions.launcher2loginserver_protocol_version,
                                        self.login_server.ip,
                                        self.login_server.port,
                                        StrictVersion(msg.version)))

    def freeze_active_server_if_empty(self):
        if len(self.players) == 0 and self.active_server.ready and not self.active_server.frozen:
            self.active_server.freeze()

    def handle_next_map_message(self, msg):
        self.logger.info(f'launcher: switching to {self.pending_server.name} on port {self.pending_server.port}')
        if self.active_server.running:
            self.logger.info(f'launcher: stopping {self.active_server.name}')
            self.active_server.stop()

        self.active_server, self.pending_server = self.pending_server, self.active_server

        self.pending_callbacks.add(self, 5, self.freeze_active_server_if_empty)

    def handle_set_player_loadouts_message(self, msg):
        self.logger.info('launcher: loadouts changed for player %d' % msg.unique_id)
        self.players[msg.unique_id] = msg.loadouts

    def handle_remove_player_loadouts_message(self, msg):
        self.logger.info('launcher: loadouts removed for player %d' % msg.unique_id)
        self.players[msg.unique_id] = None

    def handle_add_player_message(self, msg):
        if msg.ip:
            self.logger.info('launcher: login server added player %d with ip %s' % (msg.unique_id, msg.ip))
            self.firewall.modify_firewall('whitelist', 'add', msg.unique_id, msg.ip)
        else:
            self.logger.info('launcher: login server added local player %d' % msg.unique_id)

        if len(self.players) == 0 and self.active_server.frozen:
            self.active_server.unfreeze()
        self.players[msg.unique_id] = None

        # If the active server is not ready then we are between match end and the switch to the pending server.
        # It's ok to just drop this message in that case, because when the players are redirected to the pending
        # server another add_player message will come.
        if self.active_server.ready:
            self.game_controller.send(
                Launcher2GamePlayerInfo(msg.unique_id, msg.rank_xp, msg.eligible_for_first_win))

    def handle_remove_player_message(self, msg):
        if msg.ip:
            self.logger.info('launcher: login server removed player %d with ip %s' % (msg.unique_id, msg.ip))
            self.firewall.modify_firewall('whitelist', 'remove', msg.unique_id, msg.ip)
        else:
            self.logger.info('launcher: login server removed local player %d' % msg.unique_id)

        del (self.players[msg.unique_id])
        self.freeze_active_server_if_empty()

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

        if self.min_next_switch_time:
            time_left = (self.min_next_switch_time - datetime.datetime.utcnow()).total_seconds()
        else:
            time_left = 0

        if time_left > 0:
            self.pending_callbacks.add(self, time_left, self.ask_for_map_vote_result)
        else:
            self.ask_for_map_vote_result()

    def ask_for_map_vote_result(self):
        msg = Launcher2LoginWaitingForMap()
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_waiting_for_map_message = msg

    def handle_map_vote_result(self, msg):
        self.logger.info(f'launcher: received map vote result from login server: map = {msg.map_id}')
        if msg.map_id is not None:
            self.controller_context['next_map_index'] = msg.map_id
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

    def set_server_ready(self):
        self.pending_server.set_ready(True)

        self.logger.info(f'launcher: reporting {self.pending_server.name} as ready')

        msg = Launcher2LoginServerReadyMessage(self.pending_server.port, self.ports['launcherping'])
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_server_ready_message = msg

    def handle_match_time_message(self, msg):
        self.logger.info('launcher: received match time from game controller')

        msg = Launcher2LoginMatchTimeMessage(msg.seconds_remaining, msg.counting)
        if self.login_server:
            self.login_server.send(msg)
        else:
            self.last_match_time_message = msg

        if self.pending_server.running and not self.pending_server.ready:
            self.set_server_ready()

    def handle_match_end_message(self, msg):
        self.logger.info('launcher: received match end from game controller (controller context = %s)' % msg.controller_context)

        self.game_controller = None
        self.active_server.set_ready(False)
        self.controller_context = msg.controller_context

        with open(self.map_rotation_state_path, 'wt') as f:
            json.dump(self.controller_context, f)

        if 'next_map_index' in self.controller_context:
            next_map_idx = self.controller_context['next_map_index']
        else:
            next_map_idx = 0

        msg_to_login = Launcher2LoginMatchEndMessage(next_map_idx, msg.votable_maps, msg.players_time_played)
        if self.login_server:
            self.login_server.send(msg_to_login)
        else:
            self.last_match_end_message = msg_to_login

        self.min_next_switch_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=msg.next_map_wait_time)
        self.pending_server.start()

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
            try:
                loadout = self.players[player_key][class_key][loadout_key]
            except KeyError:
                # TODO: This is a temporary solution to a bug in tamods-server that causes an incorrect class to be sent ('1686')
                # We should figure out what's going on and then remove this code again.
                self.logger.warning('launcher: Incorrect params for loadout of player %d [class = %s, loadout = %s]. Sending empty loadout.' %
                                    (msg.player_unique_id, class_key, loadout_key))
                loadout = {}
        else:
            self.logger.warning('launcher: Unable to find player %d\'s loadouts. Sending empty loadout.' % msg.player_unique_id)
            loadout = {}

        msg = Launcher2GameLoadoutMessage(msg.player_unique_id,
                                          msg.class_id,
                                          loadout)
        self.game_controller.send(msg)

    def handle_game_server_terminated_message(self, msg):
        terminated_server = self.active_server if self.active_server.name == msg.server else self.pending_server
        was_already_stopping = terminated_server.stopping
        terminated_server.terminated()

        if was_already_stopping:
            self.logger.info(f'launcher: {terminated_server.name} process terminated.')
        else:
            if self.pending_server.running:
                self.logger.info(f'launcher: {terminated_server.name} process terminated unexpectedly; '
                                 f'{self.pending_server.name} already starting.')
            else:
                self.logger.info(f'launcher: {terminated_server.name} process terminated unexpectedly; '
                                 f'starting {self.pending_server.name} to take over.')
                self.pending_server.start()

            msg = Launcher2LoginServerReadyMessage(None, None)
            if self.login_server:
                self.login_server.send(msg)
            else:
                self.last_server_ready_message = msg


def handle_launcher(game_server_config, shared_config, ports, incoming_queue, server_handler_queue, data_root):
    launcher = Launcher(game_server_config, shared_config, ports, incoming_queue, server_handler_queue, data_root)
    # launcher.trace_as('launcher')
    launcher.run()
