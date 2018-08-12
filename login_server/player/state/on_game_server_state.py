#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>,
# Copyright (C) 2018 Timo Pomer <timopomer@gmail.com>
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

from ...datatypes import *
from ...firewall import modify_gameserver_whitelist, modify_loginserver_blacklist
from .player_state import handles
from .authenticated_state import AuthenticatedState


class OnGameServerState(AuthenticatedState):

    def __init__(self, player, game_server):
        super().__init__(player)
        self.game_server = game_server

    def on_enter(self):
        print("%s is entering state %s" % (self.player, type(self).__name__))
        modify_gameserver_whitelist('add', self.player, self.game_server)
        self.player.game_server = self.game_server
        self.player.game_server.set_player_loadouts(self.player)

    def on_exit(self):
        print("%s is exiting state %s" % (self.player, type(self).__name__))
        self.player.game_server.remove_player_loadouts(self.player)
        self.player.game_server = None
        modify_gameserver_whitelist('remove', self.player, self.game_server)

    @handles(packet=a00b3)
    def handle_server_disconnect(self, request):  # server disconnect
        # TODO: check on the real server if there's a response to this msg
        # serverid2 = request.findbytype(m02c4).value
        self.player.set_state(AuthenticatedState)

    @handles(packet=a018c)
    def handle_votekick(self, request):
        response = request.findbytype(m0592)

        if response is None:  # votekick initiation
            other_player = self.player.login_server.find_player_by(display_name=request.findbytype(m034a).value)

            if (other_player and
                    self.player.game_server and
                    other_player.game_server and
                    self.player.game_server == other_player.game_server and
                    self.player.game_server.playerbeingkicked is None):

                # Start a new vote
                reply = a018c()
                reply.content = [
                    m02c4().set(self.player.game_server.serverid2),
                    m034a().set(self.player.display_name),
                    m0348().set(self.player.id),
                    m02fc().set(0x0001942F),
                    m0442(),
                    m0704().set(other_player.id),
                    m0705().set(other_player.display_name)
                ]
                self.player.login_server.send_all_on_server(reply, self.player.game_server)

                for player in self.player.login_server.players.values():
                    player.vote = None
                self.player.game_server.playerbeingkicked = other_player

        else:  # votekick response
            if (self.player.game_server and
                    self.player.game_server.playerbeingkicked is not None):
                current_server = self.player.game_server

                self.player.vote = (response.value == 1)

                votes = [p.vote for p in self.player.login_server.players.values() if p.vote is not None]
                yes_votes = [v for v in votes if v]

                if len(votes) >= 1:
                    playertokick = current_server.playerbeingkicked
                    kick = len(yes_votes) >= 1

                    reply = a018c()
                    reply.content = [
                        m0348().set(playertokick.id),
                        m034a().set(playertokick.display_name)
                    ]

                    if kick:
                        reply.content.extend([
                            m02fc().set(0x00019430),
                            m0442().set(1)
                        ])

                    else:
                        reply.content.extend([
                            m02fc().set(0x00019431),
                            m0442().set(0)
                        ])

                        self.player.login_server.send_all_on_server(reply, current_server)

                    if kick:
                        # TODO: figure out if a real votekick also causes an
                        # inconsistency between the menu you see and the one
                        # you're really in
                        for msg in [a00b0(), a0035().setmainmenu(), a006f()]:
                            playertokick.send(msg)
                        playertokick.game_server = None
                        modify_gameserver_whitelist('remove', playertokick, current_server)
                        modify_loginserver_blacklist('add', playertokick)

                    current_server.playerbeingkicked = None

        # TODO: implement removal of kickvote on timeout
