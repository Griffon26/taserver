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
import random
import string

from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.datatypes import *
from common.firewall import reset_firewall
from common.ipaddresspair import IPAddressPair
from common.loginprotocol import LoginProtocolMessage
from common.messages import *
from common.statetracer import statetracer, TracingDict
from common.versions import launcher2loginserver_protocol_version
from .authcodehandler import AuthCodeRequester
from .gameserver import GameServer
from .pendingcallbacks import PendingCallbacks, ExecuteCallbackMessage
from .player.player import Player
from .player.state.unauthenticated_state import UnauthenticatedState
from .protocol_errors import ProtocolViolationError
from .utils import first_unused_number_above


@statetracer('address_pair', 'game_servers', 'players')
class LoginServer:
    def __init__(self, server_queue, client_queues, accounts, configuration):
        self.logger = logging.getLogger(__name__)
        self.server_queue = server_queue
        self.client_queues = client_queues

        self.game_servers = TracingDict()

        self.players = TracingDict()
        self.accounts = accounts
        self.message_handlers = {
            AuthCodeRequestMessage: self.handle_authcode_request_message,
            ExecuteCallbackMessage: self.handle_execute_callback_message,
            PeerConnectedMessage: self.handle_client_connected_message,
            PeerDisconnectedMessage: self.handle_client_disconnected_message,
            LoginProtocolMessage: self.handle_client_message,
            Launcher2LoginProtocolVersionMessage: self.handle_launcher_protocol_version_message,
            Launcher2LoginServerInfoMessage: self.handle_server_info_message,
            Launcher2LoginMapInfoMessage: self.handle_map_info_message,
            Launcher2LoginTeamInfoMessage: self.handle_team_info_message,
            Launcher2LoginScoreInfoMessage: self.handle_score_info_message,
            Launcher2LoginMatchTimeMessage: self.handle_match_time_message,
            Launcher2LoginServerReadyMessage: self.handle_server_ready_message,
            Launcher2LoginMatchEndMessage: self.handle_match_end_message,
        }
        self.pending_callbacks = PendingCallbacks(server_queue)

        self.address_pair, errormsg = IPAddressPair.detect()
        if not self.address_pair.external_ip:
            self.logger.warning('Unable to detect public IP address: %s\n'
                                'This will cause problems if the login server '
                                'and any players are on the same LAN, but the '
                                'game server is not.' % errormsg)
        else:
            self.logger.info('server: detected external IP: %s' % self.address_pair.external_ip)

    def run(self):
        gevent.getcurrent().name = 'loginserver'
        self.logger.info('server: login server started')
        reset_firewall('blacklist')
        while True:
            for message in self.server_queue:
                handler = self.message_handlers[type(message)]
                try:
                    handler(message)
                except Exception as e:
                    if hasattr(message, 'peer'):
                        message.peer.disconnect(e)
                    else:
                        raise

    def game_servers_for_current_mode(self, game_setting_mode: str):
        return {k: v for k, v in self.game_servers.items() if v.game_setting_mode == game_setting_mode}

    def all_game_servers(self):
        return self.game_servers

    def find_server_by_id(self, server_id):
        for game_server in self.all_game_servers().values():
            if game_server.server_id == server_id:
                return game_server
        raise ProtocolViolationError('No server found with specified server ID')

    def find_server_by_match_id(self, match_id):
        for game_server in self.all_game_servers().values():
            if game_server.match_id == match_id:
                return game_server
        raise ProtocolViolationError('No server found with specified match ID')

    def find_player_by(self, **kwargs):
        matching_players = self.find_players_by(**kwargs)

        if len(matching_players) > 1:
            raise ValueError("More than one player matched query")

        return matching_players[0] if matching_players else None

    def find_players_by(self, **kwargs):
        matching_players = self.players.values()
        for key, val in kwargs.items():
            matching_players = [player for player in matching_players if getattr(player, key) == val]

        return matching_players

    def change_player_unique_id(self, old_id, new_id):
        assert old_id in self.players
        assert new_id not in self.players

        player = self.players.pop(old_id)
        player.unique_id = new_id
        self.players[new_id] = player

    def handle_authcode_request_message(self, msg):
        authcode_requester = msg.peer

        if len(msg.login_name) > Player.max_name_length:
            self.logger.warning('server: authcode requested for a user name (%s) that is longer than '
                                '%d characters. Refused.' % (msg.login_name, Player.max_name_length))
            authcode_requester.send('Error: account names are not allowed to be longer than %d characters.' %
                                    Player.max_name_length)
        else:
            availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
            authcode = ''.join([random.choice(availablechars) for i in range(8)])
            self.logger.info('server: authcode requested for %s, returned %s' % (msg.login_name, authcode))
            self.accounts.add_account(msg.login_name, authcode)
            self.accounts.save()
            authcode_requester.send(authcode)

    def handle_execute_callback_message(self, msg):
        callback_id = msg.callback_id
        self.pending_callbacks.execute(callback_id)

    def handle_client_connected_message(self, msg):
        if isinstance(msg.peer, Player):
            unique_id = first_unused_number_above(self.players.keys(), 10000000)

            player = msg.peer
            player.unique_id = unique_id
            player.login_server = self
            player.complement_address_pair(self.address_pair)
            player.set_state(UnauthenticatedState)
            self.players[unique_id] = player
        elif isinstance(msg.peer, GameServer):
            server_id = first_unused_number_above(self.all_game_servers().keys(), 1)

            game_server = msg.peer
            game_server.server_id = server_id
            game_server.match_id = server_id + 10000000
            game_server.game_setting_mode = None
            game_server.login_server = self

            self.game_servers[server_id] = game_server

            self.logger.info('server: added game server %s (%s)' % (server_id, game_server.detected_ip))
        elif isinstance(msg.peer, AuthCodeRequester):
            pass
        else:
            assert False, "Invalid connection message received"

    def handle_client_disconnected_message(self, msg):
        if isinstance(msg.peer, Player):
            player = msg.peer
            player.disconnect()
            self.pending_callbacks.remove_receiver(player)
            player.set_state(None)
            del(self.players[player.unique_id])

        elif isinstance(msg.peer, GameServer):
            game_server = msg.peer
            self.logger.info('server: removed game server %s (%s:%s)' % (game_server.server_id,
                                                                         game_server.detected_ip,
                                                                         game_server.port))
            game_server.disconnect()
            self.pending_callbacks.remove_receiver(game_server)
            del (self.game_servers[game_server.server_id])

        elif isinstance(msg.peer, AuthCodeRequester):
            msg.peer.disconnect()

        else:
            assert False, "Invalid disconnection message received"

    def handle_client_message(self, msg):
        current_player = msg.peer
        current_player.last_received_seq = msg.clientseq

        requests = '\n'.join(['  %04X' % req.ident for req in msg.requests])
        self.logger.info('server: %s sent: %s' % (current_player, requests))

        for request in msg.requests:
            current_player.handle_request(request)

    def handle_launcher_protocol_version_message(self, msg):
        launcher_version = StrictVersion(msg.version)
        my_version = launcher2loginserver_protocol_version

        if my_version.version[0] != launcher_version.version[0]:
            game_server = msg.peer
            self.logger.warning("server: game server %s (%s) uses launcher protocol %s which is " 
                                "not compatible with this login server's protocol version %s. "
                                "Disconnecting game server..." %
                                (game_server.server_id,
                                 game_server.detected_ip,
                                 launcher_version,
                                 my_version))
            msg.peer.send(Login2LauncherProtocolVersionMessage(str(my_version)))
            msg.peer.disconnect()

    def handle_server_info_message(self, msg):
        game_server = msg.peer
        external_ip = IPv4Address(msg.external_ip) if msg.external_ip else None
        internal_ip = IPv4Address(msg.internal_ip) if msg.internal_ip else None
        address_pair = IPAddressPair(external_ip, internal_ip)

        game_server.set_info(address_pair, msg.game_setting_mode, msg.description, msg.motd)
        self.logger.info('server: server info received for %s server %s (%s)' % (game_server.game_setting_mode,
                                                                                    game_server.server_id,
                                                                                    game_server.detected_ip))

    def handle_map_info_message(self, msg):
        game_server = msg.peer
        game_server.map_id = msg.map_id

    def handle_team_info_message(self, msg):
        game_server = msg.peer
        for player_id, team_id in msg.player_to_team_id.items():
            player_id = int(player_id)
            if player_id in self.players and self.players[player_id].game_server is game_server:
                self.players[player_id].team = team_id
            else:
                self.logger.warning('server: received an invalid message from server %s about '
                                    'player %d while that player is not on that server' %
                                    (game_server.server_id, player_id))

    def handle_score_info_message(self, msg):
        game_server = msg.peer
        game_server.be_score = msg.be_score
        game_server.ds_score = msg.ds_score

    def handle_match_time_message(self, msg):
        game_server = msg.peer
        self.logger.info('server: received match time for server %s: %s seconds remaining (counting = %s)' %
              (game_server.server_id,
               msg.seconds_remaining,
               msg.counting))
        game_server.set_match_time(msg.seconds_remaining, msg.counting)

    def handle_server_ready_message(self, msg):
        game_server = msg.peer
        game_server.set_ready(msg.port)
        status = 'ready' if msg.port else 'not ready'
        self.logger.info('server: server %s (%s:%s) reports %s' % (game_server.server_id,
                                                                   game_server.detected_ip,
                                                                   game_server.port,
                                                                   status))

    def handle_match_end_message(self, msg):
        game_server = msg.peer
        self.logger.info('server: match ended on server %s.' % game_server.server_id)
