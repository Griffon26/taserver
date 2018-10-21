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
gevent.monkey.patch_all()

import json
import time
import urllib.request


from common.connectionhandler import Peer
from common.firewall import modify_firewall
from common.messages import Login2LauncherNextMapMessage, \
                            Login2LauncherSetPlayerLoadoutsMessage, \
                            Login2LauncherRemovePlayerLoadoutsMessage, \
                            Login2LauncherAddPlayer, \
                            Login2LauncherRemovePlayer, \
                            Login2LauncherPings
from common.statetracer import statetracer
from .datatypes import *
from .player.state.unauthenticated_state import UnauthenticatedState
from .player.state.authenticated_state import AuthenticatedState

PING_UPDATE_TIME = 3


@statetracer('ip', 'port', 'joinable', 'players', 'player_being_kicked',
             'match_end_time', 'match_time_counting', 'be_score', 'ds_score', 'map_id')
class GameServer(Peer):
    def __init__(self, ip):
        super().__init__()
        self.login_server = None
        self.serverid1 = None
        self.serverid2 = None
        self.ip = ip
        self.port = None
        self.description = None
        self.motd = None
        self.region = None

        self.joinable = False
        self.players = {}
        self.player_being_kicked = None
        self.match_end_time = None
        self.match_time_counting = False
        self.be_score = 0
        self.ds_score = 0
        self.map_id = 0

        response = urllib.request.urlopen('http://tools.keycdn.com/geo.json?host=%s' % self.ip)
        result = response.read()
        json_result = json.loads(result)

        continent_code_to_region = {
            'NA': REGION_NORTH_AMERICA,
            'EU': REGION_EUROPE,
            'OC': REGION_OCEANIA_AUSTRALIA
        }
        try:
            self.region = continent_code_to_region[json_result['data']['geo']['continent_code']]
        except KeyError:
            self.region = REGION_EUROPE

    def disconnect(self):
        for player in list(self.players.values()):
            player.set_state(AuthenticatedState)
        super().disconnect()

    def set_info(self, port, description, motd):
        self.port = port
        self.description = description
        self.motd = motd
        self.send_pings()

    def set_match_time(self, seconds_remaining, counting):
        self.match_end_time = int(time.time() + seconds_remaining)
        self.match_time_counting = counting
        # The game controller sends the match time only after it's properly up
        # and joinable by players
        self.joinable = True

    def get_time_remaining(self):
        if self.match_end_time is not None:
            time_remaining = int(self.match_end_time - time.time())
        else:
            time_remaining = 0

        if time_remaining < 0:
            time_remaining = 0

        return time_remaining

    def add_player(self, player):
        assert player.unique_id not in self.players
        self.players[player.unique_id] = player
        player.vote = None
        msg = Login2LauncherAddPlayer(player.unique_id, player.ip)
        self.send(msg)

    def remove_player(self, player):
        assert player.unique_id in self.players
        del self.players[player.unique_id]
        msg = Login2LauncherRemovePlayer(player.unique_id, player.ip)
        self.send(msg)

    def send_all_players(self, data):
        for player in self.players.values():
            player.send(data)

    def send_all_players_on_team(self, data, team):
        for player in self.players.values():
            if player.team == team:
                player.send(data)

    def set_player_loadouts(self, player):
        assert player.unique_id in self.players
        msg = Login2LauncherSetPlayerLoadoutsMessage(player.unique_id, player.loadouts.loadout_dict)
        self.send(msg)

    def remove_player_loadouts(self, player):
        assert player.unique_id in self.players
        msg = Login2LauncherRemovePlayerLoadoutsMessage(player.unique_id)
        self.send(msg)

    def start_next_map(self):
        self.be_score = 0
        self.ds_score = 0
        self.send(Login2LauncherNextMapMessage())

    def start_votekick(self, kicker, kickee):
        if kickee.unique_id in self.players and self.player_being_kicked is None:

            # Start a new vote
            reply = a018c()
            reply.content = [
                m02c4().set(self.serverid2),
                m034a().set(kicker.display_name),
                m0348().set(kicker.unique_id),
                m02fc().set(0x0001942F),
                m0442(),
                m0704().set(kickee.unique_id),
                m0705().set(kickee.display_name)
            ]
            self.send_all_players(reply)

            for player in self.players.values():
                player.vote = None

            self.player_being_kicked = kickee

            self.login_server.pending_callbacks.add(self, 35, self.end_votekick)

    def end_votekick(self):
        if self.player_being_kicked:
            eligible_voters, total_votes, yes_votes = self._tally_votes()
            vote_passed = total_votes >= 4 and yes_votes / total_votes >= 0.5
            self.logger.info('server: votekick %s at timeout with %d/%d/%d (yes/no/abstain) with %d players' %
                  ('passed' if vote_passed else 'failed',
                   yes_votes,
                   total_votes - yes_votes,
                   eligible_voters - total_votes,
                   len(self.players)))
            self._do_kick(vote_passed)

    def check_votes(self):
        if self.player_being_kicked:
            eligible_voters, total_votes, yes_votes = self._tally_votes()

            # If enough people vote yes, kick immediately. Otherwise wait for a majority at the timeout.
            if yes_votes >= 8:
                self.logger.info('server: votekick passed immediately %d/%d/%d (yes/no/abstain) with %d players' %
                      (yes_votes,
                       total_votes - yes_votes,
                       eligible_voters - total_votes,
                       len(self.players)))
                self._do_kick(True)

    def _tally_votes(self):
        eligible_voters_votes = {p.ip: p.vote for p in self.players.values()}
        votes = {v for v in eligible_voters_votes.values() if v is not None}
        yes_votes = [v for v in votes if v]

        return len(eligible_voters_votes), len(votes), len(yes_votes)

    def _do_kick(self, votekick_passed):
        player_to_kick = self.player_being_kicked

        reply = a018c()
        reply.content = [
            m0348().set(player_to_kick.unique_id),
            m034a().set(player_to_kick.display_name)
        ]

        if votekick_passed:
            reply.content.extend([
                m02fc().set(0x00019430),
                m0442().set(1)
            ])

        else:
            reply.content.extend([
                m02fc().set(0x00019431),
                m0442().set(0)
            ])

            self.send_all_players(reply)

        if votekick_passed:
            # TODO: figure out if a real votekick also causes an
            # inconsistency between the menu you see and the one
            # you're really in
            for msg in [a00b0(), a0035().setmainmenu(), a006f()]:
                player_to_kick.send(msg)
            player_to_kick.set_state(UnauthenticatedState)
            modify_firewall('blacklist', 'add', player_to_kick.ip)

            def remove_blacklist_rule():
                modify_firewall('blacklist', 'remove', player_to_kick.ip)

            self.login_server.pending_callbacks.add(self.login_server, 8 * 3600, remove_blacklist_rule)

        self.player_being_kicked = None

    def send_pings(self):
        player_pings = {}
        for unique_id, player in self.players.items():
            player_pings[unique_id] = player.pings[self.region] if self.region in player.pings else 999
        self.send(Login2LauncherPings(player_pings))
        self.login_server.pending_callbacks.add(self, PING_UPDATE_TIME, self.send_pings)
