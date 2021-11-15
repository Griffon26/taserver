#!/usr/bin/env python3
#
# Copyright (C) 2018-2019  Maurice van der Pot <griffon26@kfk4ever.com>
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
import hashlib
import logging
import random
import string

from common.connectionhandler import PeerConnectedMessage, PeerDisconnectedMessage
from common.datatypes import *
from common.firewall import FirewallClient
from common.ipaddresspair import IPAddressPair
from common.loginprotocol import LoginProtocolMessage
from common.messages import *
from common.statetracer import statetracer, TracingDict
from common.versions import launcher2loginserver_protocol_version
from .authcodehandler import AuthCodeRequester
from .gameserver import GameServer
from common.pendingcallbacks import PendingCallbacks, ExecuteCallbackMessage
from .player.player import Player
from .player.state.offline_state import OfflineState
from .player.state.unauthenticated_state import UnauthenticatedState
from .protocol_errors import ProtocolViolationError
from .social_network import SocialNetwork
from common import utils

UNUSED_AUTHCODE_CHECK_TIME = 3600


@statetracer('address_pair', 'game_servers', 'players')
class LoginServer:
    def __init__(self, server_queue, client_queues, server_stats_queue, ports, accounts, shared_config):
        self.logger = logging.getLogger(__name__)
        self.server_queue = server_queue
        self.client_queues = client_queues
        self.server_stats_queue = server_stats_queue

        self.game_servers = TracingDict()

        self.players = TracingDict()
        self.social_network = SocialNetwork()
        self.firewall = FirewallClient(ports, shared_config)
        self.accounts = accounts
        self.message_handlers = {
            Auth2LoginAuthCodeRequestMessage: self.handle_authcode_request_message,
            Auth2LoginChatMessage: self.handle_auth_channel_chat_message,
            Auth2LoginRegisterAsBotMessage: self.handle_register_as_bot_message,
            Auth2LoginSetEmailMessage: self.handle_set_email_message,
            ExecuteCallbackMessage: self.handle_execute_callback_message,
            HttpRequestMessage: self.handle_http_request_message,
            PeerConnectedMessage: self.handle_client_connected_message,
            PeerDisconnectedMessage: self.handle_client_disconnected_message,
            LoginProtocolMessage: self.handle_client_message,
            Launcher2LoginProtocolVersionMessage: self.handle_launcher_protocol_version_message,
            Launcher2LoginAddressInfoMessage: self.handle_address_info_message,
            Launcher2LoginServerInfoMessage: self.handle_server_info_message,
            Launcher2LoginMapInfoMessage: self.handle_map_info_message,
            Launcher2LoginTeamInfoMessage: self.handle_team_info_message,
            Launcher2LoginScoreInfoMessage: self.handle_score_info_message,
            Launcher2LoginMatchTimeMessage: self.handle_match_time_message,
            Launcher2LoginServerReadyMessage: self.handle_server_ready_message,
            Launcher2LoginMatchEndMessage: self.handle_match_end_message,
            Launcher2LoginWaitingForMap: self.handle_waiting_for_map_message,
        }
        self.pending_callbacks = PendingCallbacks(server_queue)
        self.last_player_update_time = datetime.datetime.utcnow()

        self.address_pair, errormsg = IPAddressPair.detect()
        if not self.address_pair.external_ip:
            self.logger.warning('Unable to detect public IP address: %s\n'
                                'This will cause problems if the login server '
                                'and any players are on the same LAN, but the '
                                'game server is not.' % errormsg)
        else:
            self.logger.info('detected external IP: %s' % self.address_pair.external_ip)

        self.pending_callbacks.add(self, 0, self.remove_old_authcodes)

    def remove_old_authcodes(self):
        if self.accounts.remove_old_authcodes():
            self.accounts.save()
        self.pending_callbacks.add(self, UNUSED_AUTHCODE_CHECK_TIME, self.remove_old_authcodes)

    def run(self):
        gevent.getcurrent().name = 'loginserver'
        self.logger.info('login server started')
        self.firewall.reset_firewall('blacklist')
        while True:
            for message in self.server_queue:
                handler = self.message_handlers[type(message)]
                try:
                    handler(message)
                except Exception as e:
                    if hasattr(message, 'peer'):
                        self.logger.error('an exception occurred while handling a message; passing it on to the peer...')
                        message.peer.disconnect(e)
                    else:
                        raise

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

    def find_player_by_display_name(self, display_name):
        matching_players = [p for p in self.players.values()
                            if p.display_name is not None and p.display_name.lower() == display_name.lower()]
        if matching_players:
            return matching_players[0]
        else:
            return None

    def change_player_unique_id(self, old_id, new_id):
        if new_id in self.players:
            raise AlreadyLoggedInError()

        assert old_id in self.players
        assert new_id not in self.players

        player = self.players.pop(old_id)
        player.unique_id = new_id
        self.players[new_id] = player

    def validate_username(self, username):
        if len(username) < Player.min_name_length:
            return 'User name is too short, min length is %d characters.' % Player.min_name_length

        if len(username) > Player.max_name_length:
            return 'User name is too long, max length is %d characters.' % Player.max_name_length

        try:
            ascii_bytes = username.encode('ascii')
        except UnicodeError:
            return 'User name contains invalid (i.e. non-ascii) characters'

        if not utils.is_valid_ascii_for_name(ascii_bytes):
            return 'User name contains invalid characters'

        if username.lower() == 'taserverbot':
            return 'User name is reserved'

        return None

    def send_server_stats(self):
        stats = [
            {'locked':      gs.password_hash is not None,
             'mode':        gs.game_setting_mode,
             'description': gs.description,
             'nplayers':    len(gs.players)} for gs in self.game_servers.values() if gs.joinable
        ]
        self.server_stats_queue.put(stats)

    def email_address_to_hash(self, email_address):
        email_hash = hashlib.sha256(email_address.encode('utf-8')).hexdigest()
        return email_hash

    def handle_authcode_request_message(self, msg):
        authcode_requester = msg.peer

        validation_failure = self.validate_username(msg.login_name)
        if validation_failure:
            self.logger.warning("authcode requested for invalid user name '%s': %s. Refused."
                                % (msg.login_name, validation_failure))
            authcode_requester.send('Error: %s' % validation_failure)
        else:
            availablechars = ''.join(c for c in (string.ascii_letters + string.digits) if c not in 'O0Il')
            authcode = ''.join([random.choice(availablechars) for i in range(8)])
            email_hash = self.email_address_to_hash(msg.email_address)

            if msg.login_name not in self.accounts or self.accounts[msg.login_name].email_hash == email_hash:
                self.logger.info('authcode requested for %s, returned %s' % (msg.login_name, authcode))
                self.accounts.update_account(msg.login_name, email_hash, authcode)
                self.accounts.save()

                authcode_requester.send(Login2AuthAuthCodeResultMessage(msg.source,
                                                                        msg.login_name,
                                                                        msg.email_address,
                                                                        authcode,
                                                                        None))
            else:
                authcode_requester.send(Login2AuthAuthCodeResultMessage(msg.source,
                                                                        msg.login_name,
                                                                        msg.email_address,
                                                                        None,
                                                                 'The specified email address does not match the one stored for the account'))

    def handle_auth_channel_chat_message(self, msg):
        player = self.find_player_by(login_name=msg.login_name)
        msg = a0070().set([
            m009e().set(MESSAGE_PRIVATE),
            m02e6().set(msg.text),
            m034a().set(player.display_name),
            m0574(),
            m02fe().set('taserverbot'),
            m06de().set('')
        ])
        player.send(msg)

    def handle_register_as_bot_message(self, msg):
        bot = msg.peer.authbot
        self.players[utils.AUTHBOT_ID] = bot
        bot.friends.connect_to_social_network(self.social_network)
        bot.friends.notify_online()

    def handle_set_email_message(self, msg):
        self.logger.info(f'new email set for {msg.login_name}')
        email_hash = self.email_address_to_hash(msg.email_address)
        self.accounts.update_email_hash(msg.login_name, email_hash)
        self.accounts.save()

    def handle_execute_callback_message(self, msg):
        callback_id = msg.callback_id
        self.pending_callbacks.execute(callback_id)

    def handle_client_connected_message(self, msg):
        if isinstance(msg.peer, Player):
            unique_id = utils.first_unused_number_above(self.players.keys(),
                                                        utils.MIN_UNVERIFIED_ID,
                                                        utils.MAX_UNVERIFIED_ID)

            player = msg.peer
            player.friends.connect_to_social_network(self.social_network)
            player.unique_id = unique_id
            player.login_server = self
            player.complement_address_pair(self.address_pair)
            player.set_state(UnauthenticatedState)
            self.players[unique_id] = player
        elif isinstance(msg.peer, GameServer):
            server_id = utils.first_unused_number_above(self.all_game_servers().keys(), 1)

            game_server = msg.peer
            game_server.server_id = server_id
            game_server.match_id = server_id + 10000000
            game_server.game_setting_mode = None
            game_server.login_server = self

            self.game_servers[server_id] = game_server

            self.logger.info(f'{game_server}: added')
        elif isinstance(msg.peer, AuthCodeRequester):
            pass
        else:
            assert False, "Invalid connection message received"

    def handle_client_disconnected_message(self, msg):
        if isinstance(msg.peer, Player):
            player = msg.peer
            player.disconnect()
            self.pending_callbacks.remove_receiver(player)
            player.set_state(OfflineState)
            del(self.players[player.unique_id])

        elif isinstance(msg.peer, GameServer):
            game_server = msg.peer
            self.logger.info(f'{game_server}: removed')
            game_server.disconnect()
            self.pending_callbacks.remove_receiver(game_server)
            del (self.game_servers[game_server.server_id])

        elif isinstance(msg.peer, AuthCodeRequester):
            if utils.AUTHBOT_ID in self.players and self.players[utils.AUTHBOT_ID] == msg.peer.authbot:
                msg.peer.authbot.friends.notify_offline()
            msg.peer.disconnect()

        else:
            assert False, "Invalid disconnection message received"

    def handle_client_message(self, msg):
        current_player = msg.peer
        current_player.last_received_seq = msg.clientseq

        for request in msg.requests:
            if not current_player.handle_request(request):
                self.logger.info('%s sent: %04X' % (current_player, request.ident))

        # This output is mostly for debugging of the incorrect number of players/servers online
        current_time = datetime.datetime.utcnow()
        if int((current_time - self.last_player_update_time).total_seconds()) > 15 * 60:
            self.logger.info('currently online players:\n%s' % '\n'.join([f'    {p}' for p in self.players.values()]))
            self.logger.info('currently online servers:\n%s' % '\n'.join([f'    {s}' for s in self.game_servers.values()]))
            self.last_player_update_time = current_time

    def handle_http_request_message(self, msg):
        if msg.env['PATH_INFO'] == '/status':
            if "REMOTE_ADDR" in msg.env:
                self.logger.info('Served status request via HTTP to peer "' + msg.env["REMOTE_ADDR"] + '"')
            else:
                self.logger.info('Served status request via HTTP to Unknown peer')
            msg.peer.send_response(json.dumps({
                'online_players': len(self.players),
                'online_servers': len(self.game_servers)
            }, sort_keys=True, indent=4))
        elif msg.env['PATH_INFO'] == '/detailed_status':
            if "REMOTE_ADDR" in msg.env:
                self.logger.info('Served detailed status request via HTTP to peer "' + msg.env["REMOTE_ADDR"] + '"')
            else:
                self.logger.info('Served detailed status request via HTTP to Unknown peer')
            online_game_servers_list = [
                {'locked':      gs.password_hash is not None,
                 'mode':        gs.game_setting_mode,
                 'name':        gs.description,
                 'map':         self.convert_map_id_to_map_name_and_game_type(gs.map_id)[0],
                 'type':        self.convert_map_id_to_map_name_and_game_type(gs.map_id)[1],
                 'players':     [p.display_name for p in gs.players.values()]} for gs in self.game_servers.values()
            ]
            msg.peer.send_response(json.dumps({
                'online_players_list': [p.display_name for p in self.players.values()],
                'online_servers_list': online_game_servers_list
            }, sort_keys=True, indent=4))
        else:
            msg.peer.send_response(None)

    def convert_map_id_to_map_name_and_game_type(self, map_id):
        map_names_and_types = {
            "1447": ["Katabatic","CTF"],
            "1456": ["Arx Novena","CTF"],
            "1457": ["Drydock","CTF"],
            "1458": ["Outskirts","Rabbit"],
            "1461": ["Quicksand","Rabbit"],
            "1462": ["Crossfire","CTF"],
            "1464": ["Crossfire","Rabbit"],
            "1473": ["Bella Omega","CTF"],
            "1480": ["Drydock Night","TDM"],
            "1482": ["Crossfire","TDM"],
            "1484": ["Quicksand","TDM"],
            "1485": ["Nightabatic","TDM"],
            "1487": ["Inferno","TDM"],
            "1488": ["Sulfur Cove","TDM"],
            "1490": ["Outskirts","TDM"],
            "1491": ["Inferno","Rabbit"],
            "1493": ["Temple Ruins","CTF"],
            "1494": ["Nightabatic","Rabbit"],
            "1495": ["Air Arena","Arena"],
            "1496": ["Sulfur Cove","Rabbit"],
            "1497": ["Walled In","Arena"],
            "1498": ["Lava Arena","Arena"],
            "1512": ["Tartarus","CTF"],
            "1514": ["Canyon Crusade Revival","CTF"],
            "1516": ["Raindance","CTF"],
            "1521": ["Katabatic","CaH"],
            "1522": ["Stonehenge","CTF"],
            "1523": ["Sunstar","CTF"],
            "1525": ["Drydock Night","CaH"],
            "1526": ["Outskirts 3P","CaH"],
            "1528": ["Raindance","CaH"],
            "1533": ["Hinterlands","Arena"],
            "1534": ["Permafrost","CTF"],
            "1535": ["Sulfur Cove","CaH"],
            "1536": ["Miasma","TDM"],
            "1537": ["Tartarus","CaH"],
            "1538": ["Dangerous Crossing","CTF"],
            "1539": ["Katabatic","Blitz"],
            "1540": ["Arx Novena","Blitz"],
            "1541": ["Drydock","Blitz"],
            "1542": ["Crossfire","Blitz"],
            "1543": ["Blueshift","CTF"],
            "1544": ["Whiteout","Arena"],
            "1545": ["Fraytown","Arena"],
            "1546": ["Undercroft","Arena"],
            "1548": ["Canyon Crusade Revival","CaH"],
            "1549": ["Canyon Crusade Revival","Blitz"],
            "1550": ["Bella Omega","Blitz"],
            "1551": ["Bella Omega NS","CTF"],
            "1552": ["Blueshift","Blitz"],
            "1553": ["Terminus","CTF"],
            "1554": ["Icecoaster","CTF"],
            "1555": ["Perdition","CTF"],
            "1557": ["Perdition","TDM"],
            "1558": ["Icecoaster","Blitz"],
            "1559": ["Terminus","Blitz"],
            "1560": ["Hellfire","CTF"],
            "1561": ["Hellfire","Blitz"]
        }
        return map_names_and_types.get(str(map_id), ["Unknown","Unknown"])

    def handle_launcher_protocol_version_message(self, msg):
        launcher_version = StrictVersion(msg.version)
        my_version = launcher2loginserver_protocol_version

        if my_version.version[0] != launcher_version.version[0]:
            game_server = msg.peer
            self.logger.warning(f"{game_server} uses launcher protocol {launcher_version} which is " 
                                f"not compatible with this login server's protocol version {my_version}. "
                                "Disconnecting game server...")
            msg.peer.send(Login2LauncherProtocolVersionMessage(str(my_version)))
            msg.peer.disconnect()

    def handle_address_info_message(self, msg):
        game_server = msg.peer
        external_ip = IPv4Address(msg.external_ip) if msg.external_ip else None
        internal_ip = IPv4Address(msg.internal_ip) if msg.internal_ip else None

        game_server.set_address_info(IPAddressPair(external_ip, internal_ip))
        self.logger.info(f'{game_server}: address info received')

    def handle_server_info_message(self, msg):
        game_server = msg.peer
        password_hash = bytes(msg.password_hash) if msg.password_hash is not None else None

        game_server.set_info(msg.description, msg.motd, msg.game_setting_mode, password_hash)
        self.logger.info(f'{game_server}: server info received')

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
                self.logger.warning('received an invalid message from %s about '
                                    'player %d while that player is not on that server' %
                                    (game_server, player_id))

    def handle_score_info_message(self, msg):
        game_server = msg.peer
        game_server.be_score = msg.be_score
        game_server.ds_score = msg.ds_score

    def handle_match_time_message(self, msg):
        game_server = msg.peer
        self.logger.info(f'{game_server}: received match time: {msg.seconds_remaining} seconds remaining (counting = {msg.counting})')
        game_server.set_match_time(msg.seconds_remaining, msg.counting)

    def handle_server_ready_message(self, msg):
        game_server = msg.peer
        game_server.set_ready(msg.port, msg.pingport)
        status = 'ready' if msg.port else 'not ready'
        self.logger.info(f'{game_server}: reports {status}')

    def handle_match_end_message(self, msg):
        game_server = msg.peer
        server_uptime = int((datetime.datetime.utcnow() - game_server.start_time).total_seconds())
        for player in game_server.players.values():
            if str(player.unique_id) in msg.players_time_played:
                time_played = msg.players_time_played[str(player.unique_id)]['time']
                was_win = msg.players_time_played[str(player.unique_id)]['win']

                # Cap playtime by the time the server has been active
                time_played = min(time_played, server_uptime)
                # Calculate and save the player's earned XP from this map
                player.player_settings.progression.earn_xp(time_played, was_win)

                # Update the XP in the UI
                player.send(a006d().set([
                    m04cb(),
                    m05dc().set(player.player_settings.progression.rank_xp),
                    m03ce().set(0x434D0000),
                    m00fe().set([]),
                    m0632(),
                    m0296(),
                ]))
        self.logger.info(f'{game_server}: match ended')
        game_server.initialize_map_vote(msg.next_map_idx, msg.votable_maps)

    def handle_waiting_for_map_message(self, msg):
        game_server = msg.peer
        self.logger.info(f'{game_server}: is waiting to receive the next map')
        game_server.process_map_votes()