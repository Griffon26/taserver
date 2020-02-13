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

import datetime
from common.datatypes import *
from .player_state import handles
from .authenticated_state import AuthenticatedState


class OnGameServerState(AuthenticatedState):

    def __init__(self, player, game_server):
        super().__init__(player)
        self.game_server = game_server

    def on_enter(self):
        self.logger.info("%s is entering state %s" % (self.player, type(self).__name__))
        self.player.game_server = self.game_server
        self.player.game_server.add_player(self.player)
        self.player.game_server.set_player_loadouts(self.player)
        self.player.team = None
        self.player.friends.notify_on_game_server()
        self.player.login_server.send_server_stats()

    def on_exit(self):
        self.logger.info("%s is exiting state %s" % (self.player, type(self).__name__))
        self.player.game_server.remove_player_loadouts(self.player)
        self.player.game_server.remove_player(self.player)
        self.player.game_server = None
        self.player.team = None
        self.player.login_server.send_server_stats()

    @handles(packet=a00b3)
    def handle_server_disconnect(self, request):  # server disconnect
        # TODO: check on the real server if there's a response to this msg
        self.player.set_state(AuthenticatedState)

    @handles(packet=a018c)
    def handle_votekick(self, request):
        response = request.findbytype(m0592)

        if response is None:  # votekick initiation
            other_player = self.player.login_server.find_player_by_display_name(request.findbytype(m034a).value)

            if other_player and self.player.game_server:
                self.player.game_server.start_votekick(self.player, other_player)

        else:  # votekick response
            self.player.vote = (response.value == 1)
            self.player.game_server.check_votes()
